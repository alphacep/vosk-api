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

#ifndef PROCESSOR_WETEXT_TOKEN_PARSER_H_
#define PROCESSOR_WETEXT_TOKEN_PARSER_H_

#include <set>
#include <string>
#include <unordered_map>
#include <vector>

namespace wetext {

extern const char EOS[];
extern const std::set<std::string> UTF8_WHITESPACE;
extern const std::set<std::string> ASCII_LETTERS;
extern const std::unordered_map<std::string, std::vector<std::string>>
    TN_ORDERS;
extern const std::unordered_map<std::string, std::vector<std::string>>
    ITN_ORDERS;

struct Token {
  std::string name;
  std::vector<std::string> order;
  std::unordered_map<std::string, std::string> members;

  explicit Token(const std::string& name) : name(name) {}

  void Append(const std::string& key, const std::string& value) {
    order.emplace_back(key);
    members[key] = value;
  }

  std::string String(
      const std::unordered_map<std::string, std::vector<std::string>>& orders) {
    std::string output = name + " {";
    if (orders.count(name) > 0) {
      order = orders.at(name);
    }

    for (const auto& key : order) {
      if (members.count(key) == 0) {
        continue;
      }
      output += " " + key + ": \"" + members[key] + "\"";
    }
    return output + " }";
  }
};

enum ParseType {
  kTN = 0x00,  // Text Normalization
  kITN = 0x01  // Inverse Text Normalization
};

class TokenParser {
 public:
  explicit TokenParser(ParseType type);
  std::string Reorder(const std::string& input);

 private:
  void Load(const std::string& input);
  bool Read();
  bool ParseWs();
  bool ParseChar(const std::string& exp);
  bool ParseChars(const std::string& exp);
  std::string ParseKey();
  std::string ParseValue();
  void Parse(const std::string& input);

  int index_;
  std::string ch_;
  std::vector<std::string> text_;
  std::vector<Token> tokens_;
  std::unordered_map<std::string, std::vector<std::string>> orders_;
};

}  // namespace wetext

#endif  // PROCESSOR_WETEXT_TOKEN_PARSER_H_
