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

#ifndef PROCESSOR_WETEXT_PROCESSOR_H_
#define PROCESSOR_WETEXT_PROCESSOR_H_

#include <memory>
#include <string>

#include "fst/fstlib.h"

using fst::StdArc;
using fst::StdVectorFst;
using fst::StringCompiler;
using fst::StringPrinter;

class Processor {
 public:
  Processor(const std::string& tagger_path, const std::string& verbalizer_path);
  std::string Tag(const std::string& input);
  std::string Verbalize(const std::string& input);
  std::string Normalize(const std::string& input);

 private:
  std::string ShortestPath(const StdVectorFst& lattice);
  std::string Compose(const std::string& input, const StdVectorFst* fst);

  std::shared_ptr<StdVectorFst> tagger_ = nullptr;
  std::shared_ptr<StdVectorFst> verbalizer_ = nullptr;
  std::shared_ptr<StringCompiler<StdArc>> compiler_ = nullptr;
  std::shared_ptr<StringPrinter<StdArc>> printer_ = nullptr;
};

#endif  // PROCESSOR_WETEXT_PROCESSOR_H_
