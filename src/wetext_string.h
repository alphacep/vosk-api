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

#ifndef UTILS_WETEXT_STRING_H_
#define UTILS_WETEXT_STRING_H_

#include <string>
#include <vector>

namespace wetext {
extern const char* WHITESPACE;

int UTF8CharLength(char ch);

int UTF8StringLength(const std::string& str);

void SplitUTF8StringToChars(const std::string& str,
                            std::vector<std::string>* chars);

std::string Ltrim(const std::string& str);

std::string Rtrim(const std::string& str);

std::string Trim(const std::string& str);

void Split(const std::string& str, const std::string& delim,
           std::vector<std::string>* output);

}  // namespace wetext

#endif  // UTILS_WETEXT_STRING_H_
