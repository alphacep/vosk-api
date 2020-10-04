// Copyright      2015  Johns Hopkins University (Author: Daniel Povey)

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


#ifndef VOSK_LANGUAGE_MODEL_H
#define VOSK_LANGUAGE_MODEL_H

#include <vector>
#include <map>

#include "base/kaldi-common.h"
#include "util/common-utils.h"
#include "fstext/fstext-lib.h"
#include "lat/kaldi-lattice.h"

using namespace kaldi;

// Very simply lm construction with absolute discounting

struct LanguageModelOptions {
  int32 ngram_order;  // you might want to tune this
  BaseFloat discount; // discount for backoff

  LanguageModelOptions():
      ngram_order(3),
      discount(0.5)
      { }

  void Register(OptionsItf *opts) {
    opts->Register("ngram-order", &ngram_order, "n-gram order for the phone "
                   "language model used for the 'denominator model'");
    opts->Register("discount", &discount, "Discount for backoff");
  }
};

class LanguageModelEstimator {
 public:
  LanguageModelEstimator(LanguageModelOptions &opts): opts_(opts),
                                                      num_active_lm_states_(0) {
    KALDI_ASSERT(opts.ngram_order >= 1);
  }

  // Adds counts for this sentence.  Basically does: for each n-gram in the
  // sentence, count[n-gram] += 1.  The only constraint on 'sentence' is that it
  // should contain no zeros.
  void AddCounts(const std::vector<int32> &sentence);

  // Estimates the LM and outputs it as an FST.  Note: there is
  // no concept here of backoff arcs.
  void Estimate(fst::StdVectorFst *fst);

 protected:
  struct LmState {
    // the phone history associated with this state (length can vary).
    std::vector<int32> history;

    // maps from
    std::map<int32, int32> phone_to_count;

    // total count of this state.  As we back off states to lower-order states
    // (and note that this is a hard backoff where we completely remove un-needed
    // states) this tot_count may become zero.
    int32 tot_count;

    // LM-state index of the backoff LM state (if it exists, else -1)...
    // provided for convenience.
    int32 backoff_lmstate_index;

    // this is only set after we decide on the FST state numbering (at the end).
    // If not set, it's -1.
    int32 fst_state;

    void AddCount(int32 phone, int32 count);

    // Add the contents of another LmState.
    void Add(const LmState &other);

    LmState(): tot_count(0), backoff_lmstate_index(-1),
               fst_state(-1) { }
    LmState(const LmState &other):
        history(other.history), phone_to_count(other.phone_to_count),
        tot_count(other.tot_count),
        backoff_lmstate_index(other.backoff_lmstate_index),
        fst_state(other.fst_state) { }
  };

  // maps from history to int32
  typedef unordered_map<std::vector<int32>, int32, VectorHasher<int32> > MapType;

  LanguageModelOptions opts_;

  MapType hist_to_lmstate_index_;
  std::vector<LmState> lm_states_;  // indexed by lmstate_index, the LmStates.

  // Keeps track of the number of lm states that have nonzero counts.
  int32 num_active_lm_states_;


  // adds the counts for this ngram (called from AddCounts()).
  inline void IncrementCount(const std::vector<int32> &history,
                             int32 next_phone);

  // sets up tot_count_with_parents in all the lm-states
  void SetParentCounts();

  // Finds and returns an LM-state index for a history -- or -1 if it doesn't
  // exist.  No backoff is done.
  int32 FindLmStateIndexForHistory(const std::vector<int32> &hist) const;

  // Finds and returns an LM-state index for a history -- and creates one if
  // it doesn't exist -- and also creates any backoff states needed, down
  // to history-length no_prune_ngram_order - 1.
  int32 FindOrCreateLmStateIndexForHistory(const std::vector<int32> &hist);

  // Finds and returns the most specific LM-state index for a history or
  // backed-off versions of it, that exists and has nonzero count.  Will die if
  // there is no such history.  [e.g. if there is no unigram backoff state,
  // which generally speaking there won't be.]
  int32 FindNonzeroLmStateIndexForHistory(std::vector<int32> hist) const;

  // after all backoff has been done, assigns FST state indexes to all states
  // that exist and have nonzero count.  Returns the number of states.
  int32 AssignFstStates();

  // find the FST index of the initial-state, and returns it.
  int32 FindInitialFstState() const;

  // Write to an FST
  void OutputToFst(
      int32 num_fst_states,
      fst::StdVectorFst *fst) const;

};

#endif

