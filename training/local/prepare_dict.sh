#!/usr/bin/env bash

echo "Preparing phone lists and lexicon"

src_dir=$1
dst_dir=$2

mkdir -p $dst_dir
cat $src_dir/librispeech-lexicon.txt | sed 's:[012]::g' > $dst_dir/lexicon_raw_nosil.txt

(echo SIL; echo SPN;) > $dst_dir/silence_phones.txt
echo SIL > $dst_dir/optional_silence.txt
echo "" > $dst_dir/extra_questions

cat $dst_dir/lexicon_raw_nosil.txt |  awk '{ for(n=2;n<=NF;n++){ phones[$n] = 1; }} END{for (p in phones) print p;}' | \
  grep -v SIL | sort > $dst_dir/nonsilence_phones.txt

(echo '!SIL SIL'; echo '<UNK> SPN'; ) | cat - $dst_dir/lexicon_raw_nosil.txt | sort | uniq >$dst_dir/lexicon.txt
