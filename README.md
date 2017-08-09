# Faster update calculation for gentoo

## Why

Because emerge -uDNvat @world takes up to five minutes on high-end system with SSD, that's why

## How

This script compares output of ```equery list *``` and portage ebuild files

Missing features:

* No default masks
* No slots

