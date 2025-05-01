// Copyright      2015   Johns Hopkins University (author: Daniel Povey)

// See ../../COPYING for clarification regarding multiple authors
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
//  http://www.apache.org/licenses/LICENSE-2.0
//
// THIS CODE IS PROVIDED *AS IS* BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
// KIND, EITHER EXPRESS OR IMPLIED, INCLUDING WITHOUT LIMITATION ANY IMPLIED
// WARRANTIES OR CONDITIONS OF TITLE, FITNESS FOR A PARTICULAR PURPOSE,
// MERCHANTABLITY OR NON-INFRINGEMENT.
// See the Apache 2 License for the specific language governing permissions and
// limitations under the License.

// A modified version from chain/language-model.cc for static backoff

#include <algorithm>
#include <numeric>

#include "language_model.h"

using namespace kaldi;

void LanguageModelEstimator::AddCounts(const std::vector<int32> &sentence) {
  KALDI_ASSERT(opts_.ngram_order >= 2 && "--ngram-order must be >= 2");
  int32 order = opts_.ngram_order;
  // 0 is used for left-context at the beginning of the file.. treat it as BOS.
  std::vector<int32> history(0);
  std::vector<int32>::const_iterator iter = sentence.begin(),
      end = sentence.end();
  for (; iter != end; ++iter) {
    KALDI_ASSERT(*iter != 0);
    IncrementCount(history, *iter);
    history.push_back(*iter);
    if (history.size() >= order)
      history.erase(history.begin());
  }
  // Probability of end of sentence.  This will end up getting ignored later, but
  // it still makes a difference for probability-normalization reasons.
  IncrementCount(history, 0);
}

void LanguageModelEstimator::IncrementCount(const std::vector<int32> &history,
                                            int32 next_phone) {
  int32 lm_state_index = FindOrCreateLmStateIndexForHistory(history);
  lm_states_[lm_state_index].AddCount(next_phone, 1);
}

void LanguageModelEstimator::SetParentCounts() {
  int32 num_lm_states = lm_states_.size();
  for (int32 l = 0; l < num_lm_states; l++) {
    int32 l_iter = lm_states_[l].backoff_lmstate_index;
    while (l_iter != -1) {
      lm_states_[l_iter].Add(lm_states_[l]);
      l_iter = lm_states_[l_iter].backoff_lmstate_index;
    }
  }
}

int32 LanguageModelEstimator::FindLmStateIndexForHistory(
    const std::vector<int32> &hist) const {
  MapType::const_iterator iter = hist_to_lmstate_index_.find(hist);
  if (iter == hist_to_lmstate_index_.end())
    return -1;
  else
    return iter->second;
}

int32 LanguageModelEstimator::FindNonzeroLmStateIndexForHistory(
    std::vector<int32> hist) const {
  while (1) {
    int32 l = FindLmStateIndexForHistory(hist);
    if (l == -1 || lm_states_[l].tot_count == 0) {
      // no such state or state has zero count.
      if (hist.empty())
        KALDI_ERR << "Error looking up LM state index for history "
                  << "(likely code bug)";
      hist.erase(hist.begin());  // back off.
    } else {
      return l;
    }
  }
}

int32 LanguageModelEstimator::FindOrCreateLmStateIndexForHistory(
    const std::vector<int32> &hist) {
  MapType::const_iterator iter = hist_to_lmstate_index_.find(hist);
  if (iter != hist_to_lmstate_index_.end())
    return iter->second;
  int32 ans = lm_states_.size();  // index of next element
  // next statement relies on default construct of LmState.
  lm_states_.resize(lm_states_.size() + 1);
  lm_states_.back().history = hist;
  hist_to_lmstate_index_[hist] = ans;

  // make sure backoff_lmstate_index is set
  if (hist.size() > 0) {
    std::vector<int32> backoff_hist(hist.begin() + 1,
                                    hist.end());
    int32 backoff_lm_state = FindOrCreateLmStateIndexForHistory(backoff_hist);
    lm_states_[ans].backoff_lmstate_index = backoff_lm_state;
  }
  num_active_lm_states_++;
  return ans;
}

void LanguageModelEstimator::LmState::AddCount(int32 phone, int32 count) {
  std::map<int32, int32>::iterator iter = phone_to_count.find(phone);
  if (iter == phone_to_count.end())
    phone_to_count[phone] = count;
  else
    iter->second += count;
  tot_count += count;
}

void LanguageModelEstimator::LmState::Add(const LmState &other) {
  KALDI_ASSERT(&other != this);
  std::map<int32, int32>::const_iterator iter = other.phone_to_count.begin(),
      end = other.phone_to_count.end();
  for (; iter != end; ++iter)
    AddCount(iter->first, iter->second);
}

int32 LanguageModelEstimator::AssignFstStates() {
  int32 num_lm_states = lm_states_.size();
  int32 current_fst_state = 0;
  for (int32 l = 0; l < num_lm_states; l++) {
    if (lm_states_[l].tot_count != 0) {
      lm_states_[l].fst_state = current_fst_state++;
    }
  }
  KALDI_ASSERT(current_fst_state == num_active_lm_states_);
  return current_fst_state;
}

void LanguageModelEstimator::Estimate(fst::StdVectorFst *fst) {
  KALDI_LOG << "Estimating language model with ngram-order="
            << opts_.ngram_order << ", discount="
            << opts_.discount;
  SetParentCounts();
  int32 num_fst_states = AssignFstStates();
  OutputToFst(num_fst_states, fst);
}

int32 LanguageModelEstimator::FindInitialFstState() const {
  std::vector<int32> history(0);
  int32 l = FindNonzeroLmStateIndexForHistory(history);
  KALDI_ASSERT(l != -1 && lm_states_[l].fst_state != -1);
  return lm_states_[l].fst_state;
}

void LanguageModelEstimator::OutputToFst(
    int32 num_states,
    fst::StdVectorFst *out_fst) const {
  KALDI_ASSERT(num_states == num_active_lm_states_);
  fst::StdVectorFst fst;

  for (int32 i = 0; i < num_states; i++)
    fst.AddState();
  fst.SetStart(FindInitialFstState());

  int64 tot_count = 0;
  double tot_logprob = 0.0;

  int32 num_lm_states = lm_states_.size();
  // note: not all lm-states end up being 'active'.
  for (int32 l = 0; l < num_lm_states; l++) {
    const LmState &lm_state = lm_states_[l];
    if (lm_state.fst_state == -1) {
      continue;
    }
    int32 state_count = lm_state.tot_count;
    KALDI_ASSERT(state_count != 0);
    std::map<int32, int32>::const_iterator
        iter = lm_state.phone_to_count.begin(),
        end = lm_state.phone_to_count.end();
    for (; iter != end; ++iter) {
      int32 phone = iter->first, count = iter->second;
      BaseFloat logprob = log(count * opts_.discount / state_count);
      tot_count += count;
      tot_logprob += logprob * count;
      if (phone == 0) {  // Go to final state
        fst.SetFinal(lm_state.fst_state, fst::TropicalWeight(-logprob));
      } else {  // It becomes a transition.
        std::vector<int32> next_history(lm_state.history);
        next_history.push_back(phone);
        int32 dest_lm_state = FindNonzeroLmStateIndexForHistory(next_history),
            dest_fst_state = lm_states_[dest_lm_state].fst_state;
        KALDI_ASSERT(dest_fst_state != -1);
        fst.AddArc(lm_state.fst_state,
                    fst::StdArc(phone, phone, fst::TropicalWeight(-logprob),
                                dest_fst_state));
      }
    }
    if (lm_state.backoff_lmstate_index >= 0) {
      fst.AddArc(lm_state.fst_state, fst::StdArc(0, 0, fst::TropicalWeight(-log(1 - opts_.discount)), lm_states_[lm_state.backoff_lmstate_index].fst_state));
    }
  }
  fst::DeterminizeOptions<fst::StdArc> opts;
  fst::Determinize(fst, out_fst, opts);
  fst::Connect(out_fst);
  // arc-sort.  ilabel or olabel doesn't matter, it's an acceptor.
  fst::ArcSort(out_fst, fst::ILabelCompare<fst::StdArc>());
  KALDI_LOG << "Created language model with " << out_fst->NumStates()
            << " states and " << fst::NumArcs(*out_fst) << " arcs.";
  KALDI_LOG << "Originally language model with " << fst.NumStates()
            << " states and " << fst::NumArcs(fst) << " arcs.";
}
