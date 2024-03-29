// Copyright (c) 2022 Zhendong Peng (pzd17@tsinghua.org.cn)
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
//     http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.

#include "postprocessor.h"

using fst::TokenType;

Processor::Processor(const std::string& tagger_path,
                     const std::string& verbalizer_path) {
  tagger_.reset(StdVectorFst::Read(tagger_path));
  verbalizer_.reset(StdVectorFst::Read(verbalizer_path));
  compiler_ = std::make_shared<StringCompiler<StdArc>>(TokenType::BYTE);
  printer_ = std::make_shared<StringPrinter<StdArc>>(TokenType::BYTE);
}

std::string Processor::ShortestPath(const StdVectorFst& lattice) {
  StdVectorFst shortest_path;
  fst::ShortestPath(lattice, &shortest_path, 1, true);

  std::string output;
  printer_->operator()(shortest_path, &output);
  return output;
}

std::string Processor::Compose(const std::string& input,
                               const StdVectorFst* fst) {
  StdVectorFst input_fst;
  compiler_->operator()(input, &input_fst);

  StdVectorFst lattice;
  fst::Compose(input_fst, *fst, &lattice);
  return ShortestPath(lattice);
}

std::string Processor::Tag(const std::string& input) {
  if (input.empty()) {
    return "";
  }
  return Compose(input, tagger_.get());
}

std::string Processor::Verbalize(const std::string& input) {
  if (input.empty()) {
    return "";
  }
  std::string output = Compose(input, verbalizer_.get());
  output.erase(std::remove(output.begin(), output.end(), '\0'), output.end());
  return output;
}

std::string Processor::Normalize(const std::string& input) {
  return Verbalize(Tag(input));
}


