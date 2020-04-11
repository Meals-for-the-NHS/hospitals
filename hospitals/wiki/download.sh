#!/bin/bash

# reset
>pages.list

for c in England Scotland Wales Northern_Ireland; do
	page="List_of_hospitals_in_$c"
	wget -nc "https://en.wikipedia.org/wiki/$page"
	list="$c.list" 
	python get_links.py $page >$list
	echo "found $(wc -l "$list") for $c"
	while read line; do
		wget -nc -P pages/ $line
	done <$list
done

