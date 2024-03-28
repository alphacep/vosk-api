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

#include "wetext_token_parser.h"
#include "wetext_log.h"
#include "wetext_string.h"

namespace wetext {
const char EOS[] = "<EOS>";
const std::set<std::string> UTF8_WHITESPACE = {" ", "\t", "\n", "\r",
                                               "\x0b\x0c"};
const std::set<std::string> ASCII_LETTERS = {
    "a", "b", "c", "d", "e", "f", "g", "h", "i", "j", "k", "l", "m", "n",
    "o", "p", "q", "r", "s", "t", "u", "v", "w", "x", "y", "z", "A", "B",
    "C", "D", "E", "F", "G", "H", "I", "J", "K", "L", "M", "N", "O", "P",
    "Q", "R", "S", "T", "U", "V", "W", "X", "Y", "Z", "_"};
const std::unordered_map<std::string, std::vector<std::string>> TN_ORDERS = {
    {"date", {"year", "month", "day"}},
    {"fraction", {"denominator", "numerator"}},
    {"measure", {"denominator", "numerator", "value"}},
    {"money", {"value", "currency"}},
    {"time", {"noon", "hour", "minute", "second"}}};
const std::unordered_map<std::string, std::vector<std::string>> ITN_ORDERS = {
    {"date", {"year", "month", "day"}},
    {"fraction", {"sign", "numerator", "denominator"}},
    {"measure", {"numerator", "denominator", "value"}},
    {"money", {"currency", "value", "decimal"}},
    {"time", {"hour", "minute", "second", "noon"}}};

TokenParser::TokenParser(ParseType type) {
  if (type == ParseType::kTN) {
    orders_ = TN_ORDERS;
  } else {
    orders_ = ITN_ORDERS;
  }
}

void TokenParser::Load(const std::string& input) {
  wetext::SplitUTF8StringToChars(input, &text_);
  CHECK_GT(text_.size(), 0);
  index_ = 0;
  ch_ = text_[0];
}

bool TokenParser::Read() {
  if (index_ < text_.size() - 1) {
    index_ += 1;
    ch_ = text_[index_];
    return true;
  }
  ch_ = EOS;
  return false;
}

bool TokenParser::ParseWs() {
  bool not_eos = ch_ != EOS;
  while (not_eos && ch_ == " ") {
    not_eos = Read();
  }
  return not_eos;
}

bool TokenParser::ParseChar(const std::string& exp) {
  if (ch_ == exp) {
    Read();
    return true;
  }
  return false;
}

bool TokenParser::ParseChars(const std::string& exp) {
  bool ok = false;
  std::vector<std::string> chars;
  wetext::SplitUTF8StringToChars(exp, &chars);
  for (const auto& x : chars) {
    ok |= ParseChar(x);
  }
  return ok;
}

std::string TokenParser::ParseKey() {
  CHECK_NE(ch_, EOS);
  CHECK_EQ(UTF8_WHITESPACE.count(ch_), 0);

  std::string key = "";
  while (ASCII_LETTERS.count(ch_) > 0) {
    key += ch_;
    Read();
  }
  return key;
}

std::string TokenParser::ParseValue() {
  CHECK_NE(ch_, EOS);
  bool escape = false;

  std::string value = "";
  while (ch_ != "\"") {
    value += ch_;
    escape = ch_ == "\\" && !escape;
    Read();
    if (escape) {
      value += ch_;
      Read();
    }
  }
  return value;
}

void TokenParser::Parse(const std::string& input) {
  Load(input);
  while (ParseWs()) {
    std::string name = ParseKey();
    ParseChars(" { ");

    Token token(name);
    while (ParseWs()) {
      if (ch_ == "}") {
        ParseChar("}");
        break;
      }
      std::string key = ParseKey();
      ParseChars(": \"");
      std::string value = ParseValue();
      ParseChar("\"");
      token.Append(key, value);
    }
    tokens_.emplace_back(token);
  }
}

std::string TokenParser::Reorder(const std::string& input) {
  Parse(input);
  std::string output = "";
  for (auto& token : tokens_) {
    output += token.String(orders_) + " ";
  }
  return Trim(output);
}

}  // namespace wetext
