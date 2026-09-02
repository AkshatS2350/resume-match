# Synthetic PII fixture labels

All carrier text is synthetic. Offsets are zero-based and ends are exclusive.

For the nine category carriers added below, every complete non-header line before
the `Near miss:` line is one labeled instance. Its label is the directory/category
name, its start is the line's zero-based offset, and its end is the line's exclusive
end. This compact, line-oriented form makes all 180 synthetic labels inspectable
without obscuring the near-miss cases. The test suite expands and verifies every
one of these labels against its exact carrier slice.

| carrier | category | start | end | substring |
| --- | --- | ---: | ---: | --- |
| person_name/carrier.txt | person_name | 44 | 56 | Alice Carter |
| person_name/carrier.txt | person_name | 63 | 75 | Brian Foster |
| person_name/carrier.txt | person_name | 82 | 94 | Carla Gibson |
| person_name/carrier.txt | person_name | 101 | 113 | David Harris |
| person_name/carrier.txt | person_name | 120 | 132 | Elena Jacobs |
| person_name/carrier.txt | person_name | 139 | 151 | Frank Keller |
| person_name/carrier.txt | person_name | 158 | 170 | Grace Martin |
| person_name/carrier.txt | person_name | 177 | 189 | Henry Nelson |
| person_name/carrier.txt | person_name | 196 | 208 | Irene Powell |
| person_name/carrier.txt | person_name | 215 | 227 | James Parker |
| person_name/carrier.txt | person_name | 234 | 246 | Karen Turner |
| person_name/carrier.txt | person_name | 253 | 265 | Megan Rivers |
| person_name/carrier.txt | person_name | 272 | 284 | Olivia Stone |
| person_name/carrier.txt | person_name | 291 | 303 | Peter Howard |
| person_name/carrier.txt | person_name | 310 | 322 | Quinn Miller |
| person_name/carrier.txt | person_name | 329 | 341 | Sarah Morgan |
| person_name/carrier.txt | person_name | 348 | 360 | Tessa Brooks |
| person_name/carrier.txt | person_name | 367 | 379 | Victor Allen |
| person_name/carrier.txt | person_name | 386 | 398 | Willow Hayes |
| person_name/carrier.txt | person_name | 405 | 417 | Xavier Young |
| postal_address/carrier.txt | postal_address | 49 | 84 | 101 Maple Road, Testville, CA 90210 |
| postal_address/carrier.txt | postal_address | 94 | 129 | 102 Maple Road, Testville, CA 90210 |
| postal_address/carrier.txt | postal_address | 139 | 174 | 103 Maple Road, Testville, CA 90210 |
| postal_address/carrier.txt | postal_address | 184 | 219 | 104 Maple Road, Testville, CA 90210 |
| postal_address/carrier.txt | postal_address | 229 | 264 | 105 Maple Road, Testville, CA 90210 |
| postal_address/carrier.txt | postal_address | 274 | 309 | 106 Maple Road, Testville, CA 90210 |
| postal_address/carrier.txt | postal_address | 319 | 354 | 107 Maple Road, Testville, CA 90210 |
| postal_address/carrier.txt | postal_address | 364 | 399 | 108 Maple Road, Testville, CA 90210 |
| postal_address/carrier.txt | postal_address | 409 | 444 | 109 Maple Road, Testville, CA 90210 |
| postal_address/carrier.txt | postal_address | 454 | 489 | 110 Maple Road, Testville, CA 90210 |
| postal_address/carrier.txt | postal_address | 499 | 534 | 111 Maple Road, Testville, CA 90210 |
| postal_address/carrier.txt | postal_address | 544 | 579 | 112 Maple Road, Testville, CA 90210 |
| postal_address/carrier.txt | postal_address | 589 | 624 | 113 Maple Road, Testville, CA 90210 |
| postal_address/carrier.txt | postal_address | 634 | 669 | 114 Maple Road, Testville, CA 90210 |
| postal_address/carrier.txt | postal_address | 679 | 714 | 115 Maple Road, Testville, CA 90210 |
| postal_address/carrier.txt | postal_address | 724 | 759 | 116 Maple Road, Testville, CA 90210 |
| postal_address/carrier.txt | postal_address | 769 | 804 | 117 Maple Road, Testville, CA 90210 |
| postal_address/carrier.txt | postal_address | 814 | 849 | 118 Maple Road, Testville, CA 90210 |
| postal_address/carrier.txt | postal_address | 859 | 894 | 119 Maple Road, Testville, CA 90210 |
| postal_address/carrier.txt | postal_address | 904 | 939 | 120 Maple Road, Testville, CA 90210 |
