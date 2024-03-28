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

#ifndef UTILS_WETEXT_FLAGS_H_
#define UTILS_WETEXT_FLAGS_H_

// Because openfst is a dynamic library compiled with gflags/glog, we must use
// the gflags/glog from openfst to avoid them linked both statically and
// dynamically into the executable.
#include "fst/flags.h"

#endif  // UTILS_WETEXT_FLAGS_H_
