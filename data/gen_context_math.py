#!/usr/bin/env python3
"""
Generate context fields for all math questions missing them.
Reads math.json, adds context to every question that lacks one, writes back.
"""

import json
import os

CONTEXTS = {
    # ===== TIER 1: Basic multiplication =====
    "2 x 7 = ?":
        "2 x 7 = 14. Double 7 to get 14. There are 14 days in a fortnight -- two weeks of seven days each.",
    "2 x 8 = ?":
        "2 x 8 = 16. Doubling 8 gives 16, which is also 2 to the 4th power. Computers love 16 -- it's the number of values in a single hexadecimal digit.",
    "2 x 9 = ?":
        "2 x 9 = 18. The digits of 18 add up to 9, which is true for every multiple of 9. This nifty trick works all the way up the times table.",
    "2 x 10 = ?":
        "2 x 10 = 20. Multiplying by 10 just adds a zero, and doubling that pattern makes it memorable. Twenty is the base of the Mayan number system.",
    "2 x 11 = ?":
        "2 x 11 = 22. Multiplying any single digit by 11 repeats the digit -- 11, 22, 33, and so on. It's one of the easiest patterns in all of multiplication.",
    "2 x 12 = ?":
        "2 x 12 = 24. There are 24 hours in a day, which is why the ancient Egyptians divided their day into 12 hours of light and 12 hours of darkness.",
    "3 x 3 = ?":
        "3 x 3 = 9. A number multiplied by itself is called a perfect square. 9 is the smallest odd perfect square greater than 1.",
    "3 x 4 = ?":
        "3 x 4 = 12. There are 12 months in a year, 12 notes in a musical octave, and 12 face cards in a deck. The number 12 divides evenly by 1, 2, 3, 4, and 6.",
    "3 x 5 = ?":
        "3 x 5 = 15. A quarter-hour is 15 minutes. Multiplying by 5 always ends in 0 or 5, making the 5-times table one of the friendliest to memorize.",
    "3 x 6 = ?":
        "3 x 6 = 18. You can think of it as 3 x 6 = 3 x 3 x 2 = 9 x 2 = 18. Breaking big multiplications into smaller ones is the secret to mental math.",
    "3 x 7 = ?":
        "3 x 7 = 21. In blackjack, 21 is the magic number. The digits of 21 add up to 3, confirming it's divisible by 3.",
    "3 x 8 = ?":
        "3 x 8 = 24. Think of it as triple-8 equals 24. A standard day has 24 hours -- three shifts of 8 hours each.",
    "3 x 9 = ?":
        "3 x 9 = 27. For any 9-times fact, the digits of the answer sum to 9: 2 + 7 = 9. This digit-sum trick is a quick way to verify your answer.",
    "3 x 10 = ?":
        "3 x 10 = 30. Multiplying by 10 just appends a zero. Thirty days hath September, April, June, and November.",
    "3 x 11 = ?":
        "3 x 11 = 33. Multiplying a single digit by 11 doubles the digit: 33. A quick shortcut that works for digits 1 through 9.",
    "3 x 12 = ?":
        "3 x 12 = 36. Also 6 squared! There are 36 inches in a yard, making this a handy number to know for measurement conversions.",
    "4 x 4 = ?":
        "4 x 4 = 16, a perfect square. Doubling twice is the same as multiplying by 4: 4 doubled is 8, doubled again is 16.",
    "4 x 5 = ?":
        "4 x 5 = 20. Since 4 x 5 = 20 and 20 is one-fifth of 100, this fact is the backbone of mental percentage calculations.",
    "4 x 6 = ?":
        "4 x 6 = 24. Think of it as double 12, or 4 groups of 6. There are 24 carats in pure gold.",
    "4 x 7 = ?":
        "4 x 7 = 28. There are 28 days in February (most years) and 28 dominoes in a standard double-six set.",
    "4 x 8 = ?":
        "4 x 8 = 32. Double 16, or double-double-8. A standard chess board has 32 pieces per side, and this is also 2 to the 5th power.",
    "4 x 9 = ?":
        "4 x 9 = 36. The digit-sum of 36 is 9 (3 + 6), confirming it's a multiple of 9. It's also a perfect square: 6 x 6.",
    "4 x 10 = ?":
        "4 x 10 = 40. Just append a zero when multiplying by 10. Ali Baba had 40 thieves, and the great flood lasted 40 days.",
    "4 x 11 = ?":
        "4 x 11 = 44. The 11-times trick for single digits: repeat the digit. 44 is a palindrome -- it reads the same forwards and backwards.",
    "4 x 12 = ?":
        "4 x 12 = 48. There are 48 contiguous US states. You can also think of it as 4 dozen.",
    "5 x 5 = ?":
        "5 x 5 = 25, a perfect square. Any number ending in 5 squared gives a number ending in 25 -- it's a handy pattern for quick mental math.",
    "5 x 6 = ?":
        "5 x 6 = 30. Half of 6 is 3, then append a 0 to get 30. Multiplying by 5 is the same as dividing by 2 and multiplying by 10.",
    "5 x 7 = ?":
        "5 x 7 = 35. Half of 7 is 3.5, and moving the decimal gives 35. Speed limits on many residential streets are 35 mph.",
    "5 x 8 = ?":
        "5 x 8 = 40. A standard work week is 5 days of 8 hours, totaling 40 hours. Half of 8 is 4, append a 0: 40.",
    "5 x 9 = ?":
        "5 x 9 = 45. The digits 4 + 5 = 9, confirming it's in the 9-times table. A half-right angle is 45 degrees.",
    "5 x 10 = ?":
        "5 x 10 = 50. Two nickels make a dime, and five dimes make 50 cents -- half a dollar. Multiplying by 10 always just appends a zero.",
    "5 x 11 = ?":
        "5 x 11 = 55. The speed limit on many US highways is 55 mph. The 11-times trick for single digits: just repeat the digit.",
    "5 x 12 = ?":
        "5 x 12 = 60. There are 60 minutes in an hour and 60 seconds in a minute. The ancient Babylonians used base-60, and we still feel it every time we check the clock.",

    # ===== TIER 1: Basic division =====
    "12 / 3 = ?":
        "12 / 3 = 4. Division is the inverse of multiplication: 3 x 4 = 12. If you split a dozen eggs into 3 groups, each group has 4.",
    "15 / 5 = ?":
        "15 / 5 = 3. Five goes into 15 exactly three times. A quarter has 15 minutes of clock time, which is 5 minutes per third.",
    "20 / 4 = ?":
        "20 / 4 = 5. A $20 bill split four ways gives $5 each. Division undoes multiplication: 4 x 5 = 20.",
    "24 / 3 = ?":
        "24 / 3 = 8. Splitting 24 hours into 3 equal shifts gives 8-hour shifts. The fact that 24 divides so neatly by many numbers is why we use it for timekeeping.",
    "35 / 5 = ?":
        "35 / 5 = 7. Since 5 x 7 = 35, dividing by 5 reverses the operation. All multiples of 5 end in 0 or 5, making them easy to spot.",
    "18 / 3 = ?":
        "18 / 3 = 6. The digit sum of 18 is 9, and 9 is divisible by 3, so 18 is too. This digit-sum trick works for checking divisibility by 3.",
    "16 / 4 = ?":
        "16 / 4 = 4. Dividing by 4 is the same as halving twice: 16 -> 8 -> 4. Sixteen is a perfect square and a power of 2.",
    "40 / 5 = ?":
        "40 / 5 = 8. There are 8 nickels in 40 cents. Dividing by 5 is the same as multiplying by 2 and dividing by 10.",
    "36 / 4 = ?":
        "36 / 4 = 9. Half of 36 is 18, half of 18 is 9 -- that's the halve-twice trick for dividing by 4.",
    "45 / 5 = ?":
        "45 / 5 = 9. Nine groups of five make forty-five. The digits of 45 add to 9, which is also divisible by 9.",

    # ===== TIER 1: Addition =====
    "9 + 8 = ?":
        "9 + 8 = 17. A quick trick: take 1 from the 8 to make the 9 into 10, then add the remaining 7. Making-ten is the fastest mental addition strategy.",
    "7 + 6 = ?":
        "7 + 6 = 13. Think of it as 7 + 3 + 3 = 10 + 3 = 13. Breaking numbers into parts that make 10 speeds up addition.",
    "8 + 5 = ?":
        "8 + 5 = 13. Take 2 from the 5 to make 10, then add the remaining 3. An unlucky 13, but lucky for your mental math skills.",
    "9 + 9 = ?":
        "9 + 9 = 18. Double 9 equals 18. Knowing your doubles is one of the fastest paths to mastering addition.",
    "7 + 7 = ?":
        "7 + 7 = 14. Doubles are easy to remember because they're symmetric. Two weeks is 7 + 7 = 14 days, also known as a fortnight.",
    "6 + 8 = ?":
        "6 + 8 = 14. Think of it as 6 + 4 + 4 = 10 + 4 = 14, using the make-ten strategy. You can also just double 7.",
    "9 + 7 = ?":
        "9 + 7 = 16. Take 1 from 7 to round 9 up to 10, then add the leftover 6. The make-ten trick turns hard sums into easy ones.",
    "8 + 8 = ?":
        "8 + 8 = 16. Double 8 is 16, which is also 2 to the 4th power. Doubles facts are some of the first mental math shortcuts kids learn.",

    # ===== TIER 1: Subtraction =====
    "13 - 7 = ?":
        "13 - 7 = 6. Think of it as: what plus 7 makes 13? Since 7 + 6 = 13, the answer is 6. Subtraction and addition are mirror operations.",
    "15 - 8 = ?":
        "15 - 8 = 7. Subtract 5 first to get 10, then subtract 3 more: 10 - 3 = 7. Breaking subtraction into steps through 10 makes it easier.",
    "17 - 9 = ?":
        "17 - 9 = 8. Subtracting 9 is the same as subtracting 10 and adding 1 back: 17 - 10 + 1 = 8. This near-ten trick works every time.",
    "14 - 6 = ?":
        "14 - 6 = 8. Take away 4 to reach 10, then 2 more: 10 - 2 = 8. Bridging through 10 is the core strategy for mental subtraction.",
    "16 - 7 = ?":
        "16 - 7 = 9. Subtract 6 to reach 10, then subtract 1 more. Or think: 7 + 9 = 16, so 16 - 7 = 9.",
    "18 - 9 = ?":
        "18 - 9 = 9. Half of 18 is 9. Whenever you subtract a number from its double, you get the number back.",
    "12 - 5 = ?":
        "12 - 5 = 7. Subtract 2 to get 10, then subtract 3 more. There are 7 days in a week -- a dozen minus 5.",
    "11 - 4 = ?":
        "11 - 4 = 7. Subtract 1 to reach 10, then 3 more gives 7. This bridging-through-10 strategy is the backbone of mental subtraction.",
    "20 - 8 = ?":
        "20 - 8 = 12. Starting from a round number like 20 makes subtraction easy -- no regrouping needed. Twenty minus eight is simply a dozen.",
    "15 - 6 = ?":
        "15 - 6 = 9. Take away 5 to get 10, then 1 more gives 9. Or think: 6 + 9 = 15.",

    # ===== TIER 1: Squares =====
    "1^2 = ?":
        "1 squared is 1 -- the multiplicative identity stays the same no matter how many times you multiply it. One is the loneliest (and most stable) number.",
    "2^2 = ?":
        "2 squared is 4. Squaring means multiplying a number by itself: 2 x 2 = 4. A 2x2 grid has 4 cells -- you can see the square literally.",
    "3^2 = ?":
        "3 squared is 9. A 3x3 tic-tac-toe board has 9 cells. Perfect squares grow fast: 1, 4, 9, 16, 25...",
    "4^2 = ?":
        "4 squared is 16. A 4x4 grid has 16 cells, and 16 ounces make a pound. This is also 2 to the 4th power.",
    "5^2 = ?":
        "5 squared is 25 -- a quarter of 100. Any number ending in 5 when squared ends in 25, a handy mental math pattern.",

    # ===== TIER 1: More division =====
    "10 / 2 = ?":
        "10 / 2 = 5. Splitting 10 in half gives 5. This is the most fundamental halving fact and the basis for understanding fractions.",
    "8 / 4 = ?":
        "8 / 4 = 2. Halve 8 to get 4, halve again to get 2. Dividing by 4 is the same as halving twice.",
    "9 / 3 = ?":
        "9 / 3 = 3. Nine divided by three is three -- a perfect cube root. Since 3 x 3 = 9, division simply reverses the multiplication.",
    "20 / 5 = ?":
        "20 / 5 = 4. There are 4 nickels in 20 cents. Dividing by 5 is equivalent to multiplying by 2 and dividing by 10.",
    "30 / 5 = ?":
        "30 / 5 = 6. Six groups of five make thirty. Since 30 ends in 0, it divides evenly by 5 -- no remainder.",
    "24 / 4 = ?":
        "24 / 4 = 6. Half of 24 is 12, half of 12 is 6. The halve-twice shortcut makes dividing by 4 fast and reliable.",
    "6 + 7 = ?":
        "6 + 7 = 13. Think of it as double 6 plus 1, or double 7 minus 1 -- both paths lead to 13. Near-doubles are a powerful addition strategy.",
    "9 + 6 = ?":
        "9 + 6 = 15. Take 1 from 6 to round 9 up to 10, then add the leftover 5 for 15. A quarter-hour is 15 minutes.",
    "7 + 8 = ?":
        "7 + 8 = 15. Think of it as double 7 plus 1, or double 8 minus 1. Either near-doubles approach gives you 15 quickly.",
    "11 - 6 = ?":
        "11 - 6 = 5. Subtract 1 to get 10, then 5 more from the 6 gives 5. Or just think: 6 + 5 = 11.",
    "14 - 8 = ?":
        "14 - 8 = 6. Subtract 4 to reach 10, then 4 more from the 8: 10 - 4 = 6. Bridging through 10 is the key.",
    "16 - 9 = ?":
        "16 - 9 = 7. Subtracting 9 is the same as subtracting 10 and adding 1: 16 - 10 + 1 = 7.",
    "28 / 4 = ?":
        "28 / 4 = 7. Halve 28 to get 14, halve again to get 7. February has 28 days -- exactly 4 weeks.",
    "21 / 3 = ?":
        "21 / 3 = 7. Three sevens are twenty-one, the winning hand in blackjack. The digit sum of 21 is 3, confirming divisibility.",
    "27 / 3 = ?":
        "27 / 3 = 9. And 27 is 3 cubed (3 x 3 x 3). Dividing a perfect cube by its root gives the square of that root.",
    "48 / 4 = ?":
        "48 / 4 = 12. Halve 48 to get 24, halve again to get 12. A dozen -- one of the most useful numbers in everyday life.",
    "50 / 5 = ?":
        "50 / 5 = 10. A half-dollar has the same number of nickels as a dime has pennies. Clean, round division.",
    "55 / 5 = ?":
        "55 / 5 = 11. The digits of 55 add to 10, and it divides neatly by 5. It's also the sum of the first 10 counting numbers (1+2+...+10).",
    "60 / 5 = ?":
        "60 / 5 = 12. There are 12 five-minute intervals in an hour. The Babylonian base-60 system is why our clocks use 60.",
    "44 / 4 = ?":
        "44 / 4 = 11. Halve 44 to get 22, halve again to get 11. The palindromic 44 divides neatly into the repdigit 11.",
    "33 / 3 = ?":
        "33 / 3 = 11. The digit sum of 33 is 6, divisible by 3. A third of 33 is 11 -- clean and instant.",
    "36 / 3 = ?":
        "36 / 3 = 12. Also, 36 is 6 squared, and a third of it is a dozen. There are 36 inches in a yard.",

    # ===== TIER 2: Multiplication 6-12 =====
    "6 x 6 = ?":
        "6 x 6 = 36, a perfect square. There are 36 inches in a yard and 36 keys on a small keyboard. Squaring 6 is a must-know fact.",
    "6 x 7 = ?":
        "6 x 7 = 42. Douglas Adams fans know 42 as the Answer to the Ultimate Question of Life, the Universe, and Everything.",
    "6 x 8 = ?":
        "6 x 8 = 48. Think of it as 6 x 8 = 3 x 16 = 48. There are 48 contiguous US states.",
    "6 x 9 = ?":
        "6 x 9 = 54. The 9-times finger trick: hold up 10 fingers, fold down the 6th -- you see 5 on the left, 4 on the right: 54.",
    "6 x 10 = ?":
        "6 x 10 = 60. Multiplying by 10 appends a zero. There are 60 seconds in a minute and 60 minutes in an hour.",
    "6 x 11 = ?":
        "6 x 11 = 66. Route 66 is America's most famous highway. Multiplying a single digit by 11 doubles the digit.",
    "6 x 12 = ?":
        "6 x 12 = 72. Six dozen equals 72. The average resting heart rate is about 72 beats per minute.",
    "7 x 7 = ?":
        "7 x 7 = 49. This is the only square in the 7-times table. There are 49 squares on a 7x7 grid, and 7 is considered lucky in many cultures.",
    "7 x 8 = ?":
        "7 x 8 = 56. A famous mnemonic: 56 = 7 x 8, or just remember '5, 6, 7, 8' in order. It's one of the trickiest times-table facts to memorize.",
    "7 x 9 = ?":
        "7 x 9 = 63. Fold down finger 7 and you see 6 and 3: 63. The digit sum 6 + 3 = 9 confirms it's a multiple of 9.",
    "7 x 10 = ?":
        "7 x 10 = 70. Append a zero to 7. There are 70 faces on a standard soccer ball (well, actually 32, but 70 is a pentagonal pyramidal number!).",
    "7 x 11 = ?":
        "7 x 11 = 77. A lucky double-7. The 7-Eleven convenience store chain was named for its original hours: 7 AM to 11 PM.",
    "7 x 12 = ?":
        "7 x 12 = 84. Seven dozen is 84. Think of it as 7 x 12 = 7 x 10 + 7 x 2 = 70 + 14.",
    "8 x 8 = ?":
        "8 x 8 = 64. A chess board has 64 squares, and 64 is also 2 to the 6th power. It's the smallest number that is both a perfect square and a perfect cube (other than 1).",
    "8 x 9 = ?":
        "8 x 9 = 72. The finger trick: fold down finger 8, you see 7 and 2: 72. It's also the interior angle sum of a regular pentagon's supplement.",
    "8 x 10 = ?":
        "8 x 10 = 80. Append a zero to 8. In music, 80 BPM is a common tempo marking for andante -- a walking pace.",
    "8 x 11 = ?":
        "8 x 11 = 88. A piano has 88 keys. The number 88 is considered very lucky in Chinese culture because it resembles the character for 'double happiness.'",
    "8 x 12 = ?":
        "8 x 12 = 96. Eight dozen is 96. It's also the atomic number of curium, named after Marie and Pierre Curie.",
    "9 x 9 = ?":
        "9 x 9 = 81. The largest single-digit perfect square. The digit sum 8 + 1 = 9 confirms it's a multiple of 9. A Sudoku grid has 81 cells.",
    "9 x 10 = ?":
        "9 x 10 = 90. A right angle is 90 degrees. Multiplying by 10 just appends a zero -- the simplest multiplication rule.",
    "9 x 11 = ?":
        "9 x 11 = 99. One short of 100. The digit sum 9 + 9 = 18, and 1 + 8 = 9, confirming the nine-times pattern goes all the way.",
    "9 x 12 = ?":
        "9 x 12 = 108. Nine dozen is 108. In many Eastern traditions, there are 108 prayer beads on a mala, and 108 is a Harshad number (divisible by its digit sum).",
    "10 x 10 = ?":
        "10 x 10 = 100. A perfect square and the basis of percentages. 'Per cent' literally means 'per hundred' in Latin.",
    "10 x 11 = ?":
        "10 x 11 = 110. Just append a zero to 11. In cricket, scoring 110 is called a 'ton plus ten.'",
    "10 x 12 = ?":
        "10 x 12 = 120. Ten dozen is 120, historically called a 'small gross.' It's also 5 factorial (5 x 4 x 3 x 2 x 1).",
    "11 x 11 = ?":
        "11 x 11 = 121, a palindromic perfect square. The trick for squaring 11: 1-2-1. Eleven squared reads the same forwards and backwards.",
    "11 x 12 = ?":
        "11 x 12 = 132. This is the last stop in the traditional 12x12 times table. Think of it as 11 x 12 = 11 x 10 + 11 x 2 = 110 + 22.",
    "12 x 12 = ?":
        "12 x 12 = 144, called a gross. It's also 12 squared, the crown jewel of the times table. A gross was traditionally used for counting small items like buttons and pencils.",

    # ===== TIER 2: Division =====
    "48 / 6 = ?":
        "48 / 6 = 8. Since 6 x 8 = 48, division just reverses the multiplication. Think of it as splitting 48 cookies among 6 friends.",
    "56 / 7 = ?":
        "56 / 7 = 8. Remember '5, 6, 7, 8' -- the digits go in sequence. This mnemonic makes one of the harder division facts easy.",
    "63 / 9 = ?":
        "63 / 9 = 7. The digit sum of 63 is 9, confirming divisibility by 9. The finger trick for 9 x 7 gives 63, so dividing reverses it.",
    "72 / 8 = ?":
        "72 / 8 = 9. Since 8 x 9 = 72, this is its mirror fact. Seventy-two is a popular number in finance -- the 'Rule of 72' estimates how long it takes money to double.",
    "84 / 12 = ?":
        "84 / 12 = 7. Seven dozen is 84. Dividing by 12 reverses the dozens multiplication.",
    "66 / 6 = ?":
        "66 / 6 = 11. Route 66 divided into 6 equal stretches gives 11 each. The repeating digit pattern of 66 makes this division quick.",
    "77 / 7 = ?":
        "77 / 7 = 11. Double-seven divided by single-seven is 11. The repeating digit makes this one of the easiest division facts.",
    "88 / 8 = ?":
        "88 / 8 = 11. Eighty-eight piano keys divided by 8 gives 11. Dividing any 'double digit' number (like 88) by its digit always yields 11.",
    "99 / 9 = ?":
        "99 / 9 = 11. One step below 100, and cleanly divisible by 9. The digit sum of 99 is 18, and 1 + 8 = 9, confirming divisibility.",
    "108 / 9 = ?":
        "108 / 9 = 12. The digit sum of 108 is 9, confirming it's divisible by 9. There are 108 beads on a Buddhist mala.",
    "96 / 8 = ?":
        "96 / 8 = 12. Halve 96 to get 48, halve to get 24, halve to get 12. Dividing by 8 is the same as halving three times.",
    "72 / 6 = ?":
        "72 / 6 = 12. Six dozen is 72. The average resting heart beats 72 times per minute -- that's 12 beats every 10 seconds.",

    # ===== TIER 2: Squares =====
    "6^2 = ?":
        "6 squared is 36. A 6x6 grid has 36 cells. Knowing perfect squares helps you estimate square roots and recognize patterns in algebra.",
    "7^2 = ?":
        "7 squared is 49. A 7x7 grid has 49 cells. This is the only perfect square in the 40s, making it a handy landmark number.",
    "8^2 = ?":
        "8 squared is 64. A chess board is an 8x8 grid with 64 squares. It's also 2^6, connecting squares and powers of 2.",
    "9^2 = ?":
        "9 squared is 81. A Sudoku grid is 9x9 = 81 cells. The digit sum of 81 is 9, confirming the nine-times connection.",
    "10^2 = ?":
        "10 squared is 100. This is the foundation of the percentage system -- 'per cent' means 'per hundred.' It's the most commonly used perfect square.",
    "11^2 = ?":
        "11 squared is 121, a palindrome. The 11-squaring trick: put a 1 on each end and a 2 in the middle. Palindromic squares are rare and beautiful.",
    "12^2 = ?":
        "12 squared is 144, also called a gross. This is the largest fact in the standard 12x12 times table, and knowing it is a badge of multiplication mastery.",

    # ===== TIER 2: Fractions of numbers =====
    "1/2 of 48 = ?":
        "Half of 48 is 24. Just divide by 2. Halving is the most fundamental fraction operation and the basis for finding quarters and eighths.",
    "1/2 of 36 = ?":
        "Half of 36 is 18. Think: 36 / 2 = 18. Halving even numbers is instant -- just halve each digit pair.",
    "1/2 of 70 = ?":
        "Half of 70 is 35. Halve the 7 to get 3.5, then shift: 35. This works because 70 = 2 x 35.",
    "1/4 of 60 = ?":
        "One-quarter of 60 is 15. Halve 60 to get 30, halve again to get 15. A quarter-hour is 15 minutes for exactly this reason.",
    "1/4 of 80 = ?":
        "One-quarter of 80 is 20. Halve 80 to get 40, halve again to get 20. Dividing by 4 always means halving twice.",
    "1/4 of 100 = ?":
        "One-quarter of 100 is 25. A quarter (the coin) is 25 cents -- literally one-quarter of a dollar. This is the most practical fraction fact in daily life.",
    "3/4 of 40 = ?":
        "Three-quarters of 40 is 30. Find 1/4 first (40 / 4 = 10), then multiply by 3: 10 x 3 = 30. Breaking fractions into steps makes them easy.",
    "3/4 of 80 = ?":
        "Three-quarters of 80 is 60. One-quarter is 20, so three-quarters is 60. Think of it as 80 minus one-quarter of 80.",
    "1/3 of 90 = ?":
        "One-third of 90 is 30. Since 3 x 30 = 90, the division is clean. A third of 90 degrees is the angle of an equilateral triangle's corner.",
    "1/3 of 60 = ?":
        "One-third of 60 is 20. There are 20 minutes in a third of an hour. The Babylonian base-60 system makes these divisions especially clean.",

    # ===== TIER 2: Percentages =====
    "25% of 80 = ?":
        "25% of 80 = 20. Twenty-five percent means one-quarter, so divide by 4. This is equivalent to 80 / 4 = 20.",
    "25% of 120 = ?":
        "25% of 120 = 30. One quarter of 120 is 30. Halve to get 60, halve again to get 30 -- the double-half trick for 25%.",
    "50% of 90 = ?":
        "50% of 90 = 45. Fifty percent is just half. Half of 90 is 45, which is also the angle of a perfect diagonal.",
    "50% of 130 = ?":
        "50% of 130 = 65. Half of 130 is 65. To halve an odd-tens number, halve the hundreds and add 5: 50 + 15... or just think 130/2.",
    "10% of 350 = ?":
        "10% of 350 = 35. Finding 10% is the easiest percentage -- just move the decimal point one place left. This is the anchor for calculating any percentage mentally.",
    "10% of 520 = ?":
        "10% of 520 = 52. Move the decimal one place left: 520 becomes 52. From 10% you can quickly find 5% (26), 20% (104), or any multiple.",
    "75% of 40 = ?":
        "75% of 40 = 30. Seventy-five percent is three-quarters. Find a quarter (10), then triple it (30). Or subtract a quarter from the whole: 40 - 10 = 30.",
    "75% of 60 = ?":
        "75% of 60 = 45. One quarter is 15, so three quarters is 45. Three-quarters of an hour is also 45 minutes.",
    "10% of 70 = ?":
        "10% of 70 = 7. Just move the decimal one place left. Seven is one-tenth of seventy -- clean and instant.",
    "50% of 44 = ?":
        "50% of 44 = 22. Half of 44 is 22. Both are palindromic numbers, and halving even numbers is always straightforward.",

    # ===== TIER 2: More multiplication =====
    "9 x 6 = ?":
        "9 x 6 = 54. The finger trick: fold down finger 6 to see 5 on the left and 4 on the right: 54. The digit sum 5 + 4 = 9 confirms it.",
    "6 x 4 = ?":
        "6 x 4 = 24. Double 12, or 6 groups of 4. There are 24 hours in a day, 24 carats in pure gold.",
    "7 x 4 = ?":
        "7 x 4 = 28. Four weeks have 28 days. Double 7 is 14, double again is 28 -- multiplying by 4 means doubling twice.",
    "8 x 4 = ?":
        "8 x 4 = 32. Double 8 is 16, double 16 is 32. This is also 2 to the 5th power, a key number in computing.",
    "9 x 4 = ?":
        "9 x 4 = 36. Double 9 is 18, double again is 36. It's also 6 squared -- where the 4-times and 9-times tables meet a perfect square.",
    "7 x 6 = ?":
        "7 x 6 = 42. The Answer to Life, the Universe, and Everything, according to The Hitchhiker's Guide. Also 6 x 7 by commutativity.",
    "8 x 6 = ?":
        "8 x 6 = 48. Think of it as 8 x 3 x 2 = 24 x 2 = 48. The 48 contiguous US states help you remember this one.",
    "12 x 6 = ?":
        "12 x 6 = 72. Half a gross (144/2). The normal human heart rate is about 72 beats per minute.",
    "12 x 7 = ?":
        "12 x 7 = 84. Seven dozen. Think 12 x 7 = 12 x 5 + 12 x 2 = 60 + 24 = 84.",
    "12 x 8 = ?":
        "12 x 8 = 96. Eight dozen. Think 12 x 8 = 12 x 10 - 12 x 2 = 120 - 24 = 96.",
    "12 x 9 = ?":
        "12 x 9 = 108. Nine dozen. A Harshad number: 108 is divisible by its digit sum (1+0+8=9). There are 108 beads on a traditional mala.",
    "12 x 11 = ?":
        "12 x 11 = 132. Eleven dozen. The 11-times trick for two digits: split, add, insert. 1(1+2)2 = 132.",
    "11 x 6 = ?":
        "11 x 6 = 66. The single-digit-times-11 trick: repeat the digit. Route 66 runs from Chicago to Santa Monica.",
    "11 x 7 = ?":
        "11 x 7 = 77. Double-lucky sevens. The 11-times rule for single digits makes this instant: just write 7 twice.",
    "11 x 8 = ?":
        "11 x 8 = 88. A piano has 88 keys. The 11-times trick: repeat the 8. In Chinese, 88 sounds like 'double fortune.'",
    "11 x 9 = ?":
        "11 x 9 = 99. One short of 100. The 11-times trick gives double-9, and the digit sum (18) confirms it's a multiple of 9.",

    # ===== TIER 2: More division =====
    "56 / 8 = ?":
        "56 / 8 = 7. The '5-6-7-8' mnemonic works in reverse too. Since 7 x 8 = 56, dividing by 8 gives 7.",
    "42 / 6 = ?":
        "42 / 6 = 7. The Answer to Everything divided by 6 is 7. Since 6 x 7 = 42, division is just the reverse.",
    "54 / 6 = ?":
        "54 / 6 = 9. Since 6 x 9 = 54, dividing reverses it. The digit sum of 54 is 9, confirming it's in the 9-times table too.",
    "70 / 7 = ?":
        "70 / 7 = 10. A clean division -- 7 goes into 70 exactly 10 times. Any number times 10 just appends a zero, so reversal is easy.",
    "90 / 9 = ?":
        "90 / 9 = 10. Nine goes into ninety exactly ten times. A right angle (90 degrees) divided into 9 equal parts gives 10-degree slices.",
    "110 / 11 = ?":
        "110 / 11 = 10. Eleven goes into 110 exactly ten times. Since 11 x 10 = 110, the division is straightforward.",
    "120 / 12 = ?":
        "120 / 12 = 10. Ten dozen is 120. Also, 120 is 5 factorial (5!), and dividing by a dozen gives a nice round 10.",
    "49 / 7 = ?":
        "49 / 7 = 7. Dividing a perfect square by its root returns the root. 49 = 7 x 7, so 49 / 7 = 7.",
    "81 / 9 = ?":
        "81 / 9 = 9. Since 81 is 9 squared, dividing by 9 gives 9 back. A Sudoku grid's 81 cells split into 9 rows of 9.",
    "64 / 8 = ?":
        "64 / 8 = 8. Since 64 is 8 squared, dividing by 8 returns 8. A chessboard's 64 squares split into 8 rows of 8.",
    "36 / 6 = ?":
        "36 / 6 = 6. A perfect square divided by its root returns the root. 36 = 6 x 6, so 36 / 6 = 6.",
    "144 / 12 = ?":
        "144 / 12 = 12. A gross (144) divided by a dozen gives a dozen. Since 144 = 12 x 12, dividing by 12 returns 12.",
    "132 / 11 = ?":
        "132 / 11 = 12. Eleven dozen is 132. Dividing by 11: the digits of 132 follow the 11-times pattern (1, 1+2=3, 2).",
    "10% of 200 = ?":
        "10% of 200 = 20. Move the decimal one place left: 200 becomes 20. Ten percent is the anchor percentage for all mental calculations.",

    # ===== TIER 3: Geometry - Rectangles =====
    "Area of a rectangle: length x ___?":
        "Area equals length times width. This formula works because you're counting how many unit squares fit inside the rectangle -- rows times columns.",
    "Area of a rectangle 6 x 9 = ?":
        "Area = 6 x 9 = 54 square units. Picture a grid of 6 rows and 9 columns -- count the cells and you get 54.",
    "Area of a rectangle 7 x 8 = ?":
        "Area = 7 x 8 = 56 square units. The '5-6-7-8' mnemonic helps here: 56 = 7 x 8.",
    "Area of a rectangle 5 x 12 = ?":
        "Area = 5 x 12 = 60 square units. Five dozen unit squares. Half of 12 is 6, times 10 is 60 -- the halve-and-double shortcut.",
    "Area of a rectangle 10 x 4 = ?":
        "Area = 10 x 4 = 40 square units. Multiplying by 10 just appends a zero. A 10x4 rectangle is common in floor tiles.",
    "Perimeter of a rectangle 5 x 4 = ?":
        "Perimeter = 2(5 + 4) = 2 x 9 = 18 units. Perimeter is the total distance around all four sides, computed as 2 times length plus width.",
    "Perimeter of a rectangle 6 x 3 = ?":
        "Perimeter = 2(6 + 3) = 2 x 9 = 18 units. Same perimeter as 5x4! Different rectangles can share the same perimeter but have different areas.",
    "Perimeter of a rectangle 8 x 5 = ?":
        "Perimeter = 2(8 + 5) = 2 x 13 = 26 units. Add the two side lengths, then double. The perimeter tells you how much fencing you'd need.",
    "Perimeter of a rectangle 7 x 7 = ?":
        "Perimeter = 2(7 + 7) = 28 units. A rectangle with equal sides is a square! For a square, perimeter = 4 x side = 4 x 7 = 28.",

    # ===== TIER 3: Triangles =====
    "Area of a triangle = 1/2 x base x ___?":
        "Area of a triangle = 1/2 x base x height. A triangle is half of a rectangle with the same base and height -- that's where the 1/2 comes from.",
    "Area of a triangle: base=8, height=5 = ?":
        "Area = 1/2 x 8 x 5 = 20 square units. The full rectangle would be 40; the triangle is exactly half.",
    "Area of a triangle: base=6, height=4 = ?":
        "Area = 1/2 x 6 x 4 = 12 square units. Half of 24. A triangle always takes up exactly half the space of its bounding rectangle.",
    "Area of a triangle: base=10, height=6 = ?":
        "Area = 1/2 x 10 x 6 = 30 square units. The rectangle would be 60; halving gives 30. Ten times any number, then halve -- easy mental math.",
    "Area of a triangle: base=9, height=4 = ?":
        "Area = 1/2 x 9 x 4 = 18 square units. Half of 36. You can also think of it as 9 x 2 = 18 by halving the 4 first.",

    # ===== TIER 3: Circles =====
    "Circumference of a circle = 2 x pi x ___?":
        "Circumference = 2 x pi x radius. The constant pi (about 3.14159) is the ratio of circumference to diameter, so C = pi x d = 2 x pi x r.",
    "Area of a circle = pi x ___^2?":
        "Area = pi x r^2. The radius is squared because area is two-dimensional. Doubling the radius quadruples the area -- a powerful geometric insight.",
    "The diameter of a circle = 2 x ___?":
        "Diameter = 2 x radius. The diameter is the longest chord of a circle, passing through the center. It's always exactly twice the radius.",
    "Circumference = pi x ___?":
        "Circumference = pi x diameter. This is the original definition of pi: the ratio of any circle's circumference to its diameter, roughly 3.14159.",

    # ===== TIER 3: Square roots =====
    "sqrt1 = ?":
        "The square root of 1 is 1. One times one is one -- the multiplicative identity is its own square root.",
    "sqrt4 = ?":
        "The square root of 4 is 2, because 2 x 2 = 4. Four is the smallest perfect square greater than 1.",
    "sqrt9 = ?":
        "The square root of 9 is 3, because 3 x 3 = 9. A tic-tac-toe board has sqrt(9) = 3 rows and 3 columns.",
    "sqrt16 = ?":
        "The square root of 16 is 4, because 4 x 4 = 16. Sixteen is both a perfect square and a power of 2 (2^4).",
    "sqrt25 = ?":
        "The square root of 25 is 5, because 5 x 5 = 25. A quarter of 100, and its root is a quarter of 20.",
    "sqrt36 = ?":
        "The square root of 36 is 6, because 6 x 6 = 36. There are 36 inches in a yard.",
    "sqrt49 = ?":
        "The square root of 49 is 7, because 7 x 7 = 49. This is the only perfect square in the 40s.",
    "sqrt64 = ?":
        "The square root of 64 is 8, because 8 x 8 = 64. A chessboard has 64 squares arranged in an 8x8 grid.",
    "sqrt81 = ?":
        "The square root of 81 is 9, because 9 x 9 = 81. A Sudoku grid has 81 cells in a 9x9 arrangement.",
    "sqrt100 = ?":
        "The square root of 100 is 10, because 10 x 10 = 100. The basis of our decimal system and percentages.",
    "sqrt121 = ?":
        "The square root of 121 is 11, because 11 x 11 = 121. It's a palindromic perfect square -- reading 121 backwards still gives 121.",
    "sqrt144 = ?":
        "The square root of 144 is 12, because 12 x 12 = 144. A gross (144) is the square of a dozen, the crown of the times table.",

    # ===== TIER 3: Basic algebra =====
    "If 3x = 21, then x = ?":
        "Divide both sides by 3: x = 21/3 = 7. Solving a one-step equation means undoing the operation -- multiplication undoes with division.",
    "If x + 9 = 15, then x = ?":
        "Subtract 9 from both sides: x = 15 - 9 = 6. Addition undoes with subtraction, keeping the equation balanced like a scale.",
    "If 5x = 35, then x = ?":
        "Divide both sides by 5: x = 35/5 = 7. Since 5 x 7 = 35, you're just reading the times table backwards.",
    "If x - 4 = 11, then x = ?":
        "Add 4 to both sides: x = 11 + 4 = 15. To undo subtraction, add. The inverse operation restores the original value.",
    "If 8x = 56, then x = ?":
        "Divide both sides by 8: x = 56/8 = 7. Remember '5-6-7-8' -- the digits in sequence encode this times-table fact.",
    "If x + 13 = 20, then x = ?":
        "Subtract 13 from both sides: x = 20 - 13 = 7. Think: what do I add to 13 to reach 20?",
    "If 4x = 48, then x = ?":
        "Divide both sides by 4: x = 48/4 = 12. Since 4 x 12 = 48, this is just the times table in reverse.",
    "If x / 6 = 9, then x = ?":
        "Multiply both sides by 6: x = 9 x 6 = 54. Division undoes with multiplication. The finger trick for 9 x 6 gives 54.",
    "If 9x = 72, then x = ?":
        "Divide both sides by 9: x = 72/9 = 8. The digit sum of 72 is 9, confirming it's a multiple of 9.",
    "If x - 7 = 14, then x = ?":
        "Add 7 to both sides: x = 14 + 7 = 21. Undoing subtraction with addition: the fundamental balancing act of algebra.",

    # ===== TIER 3: Order of operations =====
    "3 + 4 x 2 = ?":
        "Multiplication before addition: 4 x 2 = 8, then 3 + 8 = 11. PEMDAS says multiply and divide before adding and subtracting.",
    "10 - 2 x 3 = ?":
        "Multiply first: 2 x 3 = 6, then 10 - 6 = 4. Without order-of-operations rules, you'd get 24 -- completely different!",
    "5 x 3 + 2 = ?":
        "Multiply first: 5 x 3 = 15, then 15 + 2 = 17. The multiplication happens before addition, following PEMDAS.",
    "8 + 6 / 2 = ?":
        "Divide first: 6 / 2 = 3, then 8 + 3 = 11. Division has the same priority as multiplication, both before addition.",
    "12 / 4 + 5 = ?":
        "Divide first: 12 / 4 = 3, then 3 + 5 = 8. Without PEMDAS, you might incorrectly divide 12 by 9.",
    "2 x (3 + 4) = ?":
        "Parentheses first: 3 + 4 = 7, then 2 x 7 = 14. Parentheses override the default order -- they're the 'P' in PEMDAS.",
    "3 x (5 - 2) = ?":
        "Parentheses first: 5 - 2 = 3, then 3 x 3 = 9. Parentheses force the subtraction to happen before multiplication.",
    "(8 + 2) x 3 = ?":
        "Parentheses first: 8 + 2 = 10, then 10 x 3 = 30. Without parentheses, it would be 8 + 6 = 14 -- a very different answer.",
    "20 / (2 + 3) = ?":
        "Parentheses first: 2 + 3 = 5, then 20 / 5 = 4. The parentheses make 5 the denominator, not 2.",
    "6 + 3^2 = ?":
        "Exponents before addition: 3^2 = 9, then 6 + 9 = 15. In PEMDAS, exponents come right after parentheses and before multiplication.",

    # ===== TIER 3: Squares and perimeters =====
    "Area of a square with side 7 = ?":
        "Area = 7 x 7 = 49 square units. For a square, area is simply side squared. A 7x7 grid has 49 cells.",
    "Area of a square with side 9 = ?":
        "Area = 9 x 9 = 81 square units. A Sudoku grid is exactly this: 81 cells in a 9x9 square.",
    "Perimeter of a square with side 6 = ?":
        "Perimeter = 4 x 6 = 24 units. A square has four equal sides, so perimeter is just 4 times the side length.",
    "Perimeter of a square with side 8 = ?":
        "Perimeter = 4 x 8 = 32 units. Walking around a square means traversing 4 equal sides. Think of it as doubling 16.",
    "Area of a rectangle 11 x 3 = ?":
        "Area = 11 x 3 = 33 square units. Eleven groups of 3, or three groups of 11 -- multiplication is commutative.",
    "Perimeter of a rectangle 10 x 6 = ?":
        "Perimeter = 2(10 + 6) = 2 x 16 = 32 units. Add the two different side lengths, then double for all four sides.",
    "If 12x = 144, then x = ?":
        "Divide both sides by 12: x = 144/12 = 12. Since 12 x 12 = 144 (a gross), x equals 12. A perfect square equation.",
    "If x / 4 = 7, then x = ?":
        "Multiply both sides by 4: x = 7 x 4 = 28. Multiplication undoes division. There are 28 days in exactly 4 weeks.",
    "If 7x = 63, then x = ?":
        "Divide both sides by 7: x = 63/7 = 9. The digit sum of 63 is 9, confirming it's a multiple of both 7 and 9.",
    "4 x 5 - 6 = ?":
        "Multiply first: 4 x 5 = 20, then 20 - 6 = 14. PEMDAS ensures multiplication happens before subtraction.",
    "15 / 3 + 7 = ?":
        "Divide first: 15 / 3 = 5, then 5 + 7 = 12. Division has priority over addition in the order of operations.",
    "2 + 3 x 4 = ?":
        "Multiply first: 3 x 4 = 12, then 2 + 12 = 14. A classic PEMDAS trap -- many people incorrectly add first to get 20.",
    "Area of a triangle: base=12, height=5 = ?":
        "Area = 1/2 x 12 x 5 = 30 square units. Half of 60. The triangle formula always gives half the area of the corresponding rectangle.",
    "Area of a rectangle 3 x 15 = ?":
        "Area = 3 x 15 = 45 square units. Think of it as 3 x 10 + 3 x 5 = 30 + 15 = 45. The distributive property at work.",
    "Perimeter of a rectangle 9 x 2 = ?":
        "Perimeter = 2(9 + 2) = 2 x 11 = 22 units. A long, thin rectangle -- like a bookmark or a ruler.",
    "If x + 25 = 40, then x = ?":
        "Subtract 25 from both sides: x = 40 - 25 = 15. Think: a quarter from 40 leaves 15.",
    "(4 + 6) x (3 - 1) = ?":
        "Evaluate both parentheses: 10 x 2 = 20. Parentheses first, then multiply the results. Two pairs of parentheses, two steps.",
    "5^2 - 4^2 = ?":
        "25 - 16 = 9. This is also (5+4)(5-4) = 9 x 1 = 9 using the difference of squares identity: a^2 - b^2 = (a+b)(a-b).",
    "Area of a triangle: base=14, height=3 = ?":
        "Area = 1/2 x 14 x 3 = 21 square units. Halve the base first: 14/2 = 7, then 7 x 3 = 21.",
    "Perimeter of a square with side 11 = ?":
        "Perimeter = 4 x 11 = 44 units. Four equal sides of 11 each. The result is a palindromic number.",
    "If x - 16 = 9, then x = ?":
        "Add 16 to both sides: x = 9 + 16 = 25. Twenty-five is also 5 squared -- a perfect square lurking in algebra.",
    "3 x 4^2 = ?":
        "Exponents first: 4^2 = 16, then 3 x 16 = 48. Without the exponent rule, you'd incorrectly get 12^2 = 144.",
    "Area of a rectangle 8 x 7 = ?":
        "Area = 8 x 7 = 56 square units. The '5-6-7-8' sequence: 56 = 7 x 8.",
    "Perimeter of a rectangle 12 x 5 = ?":
        "Perimeter = 2(12 + 5) = 2 x 17 = 34 units. Add the two sides, then double.",
    "sqrt25 x sqrt4 = ?":
        "sqrt(25) x sqrt(4) = 5 x 2 = 10. The square root of a product equals the product of the square roots: sqrt(25 x 4) = sqrt(100) = 10.",
    "6 x 4 - 3 x 5 = ?":
        "Multiply first: 24 - 15 = 9. Both multiplications happen before subtraction. PEMDAS handles left-to-right among equal precedence.",

    # ===== TIER 4: Volume =====
    "Volume of a rectangular box: length x width x ___?":
        "Volume = length x width x height. You're counting how many unit cubes fit inside -- layers of unit squares stacked up.",
    "Volume of a cube with side 4 = ?":
        "4^3 = 64 cubic units. A cube's volume is side cubed. This is also 2^6, connecting it to binary computing.",
    "Volume of a cube with side 3 = ?":
        "3^3 = 27 cubic units. A Rubik's cube is 3x3x3 = 27 smaller cubes. This is why 27 is called a perfect cube.",
    "Volume of a cube with side 5 = ?":
        "5^3 = 125 cubic units. Five cubed is 125. This is also 1000/8 -- an eighth of a cubic meter in centimeters.",
    "Volume of a cube with side 2 = ?":
        "2^3 = 8 cubic units. The smallest cube bigger than a single unit. Eight is 2 cubed and also the number of corners on any cube.",
    "Volume of a box 3 x 4 x 5 = ?":
        "3 x 4 x 5 = 60 cubic units. Multiply in steps: 3 x 4 = 12, then 12 x 5 = 60. Each dimension adds another multiplicative layer.",
    "Volume of a box 2 x 6 x 7 = ?":
        "2 x 6 x 7 = 84 cubic units. Start with 2 x 6 = 12, then 12 x 7 = 84. Seven dozen unit cubes fill this box.",
    "Volume of a cylinder = pi x r^2 x ___?":
        "Volume = pi x r^2 x h (height). A cylinder is a circle extruded through its height, so its volume is the circle's area times height.",
    "Surface area of a cube with side 3 = ?":
        "SA = 6 x 3^2 = 6 x 9 = 54 square units. A cube has 6 faces, each a square of area s^2. Six nines make 54.",
    "Surface area of a cube with side 4 = ?":
        "SA = 6 x 4^2 = 6 x 16 = 96 square units. Six faces of 16 square units each. Surface area grows with the square, volume with the cube.",
    "Surface area of a cube with side 2 = ?":
        "SA = 6 x 2^2 = 6 x 4 = 24 square units. The smallest non-trivial cube surface area. Like unfolding a die into its 6 faces.",

    # ===== TIER 4: Pythagorean theorem =====
    "A right triangle has legs 3 and 4. Hypotenuse = ?":
        "sqrt(9 + 16) = sqrt(25) = 5. The 3-4-5 triangle is the most famous Pythagorean triple, known since ancient Babylon over 3,800 years ago.",
    "A right triangle has legs 5 and 12. Hypotenuse = ?":
        "sqrt(25 + 144) = sqrt(169) = 13. The 5-12-13 triple is the second-most common Pythagorean triple. All three numbers are the hypotenuse of nested triples.",
    "A right triangle has legs 8 and 6. Hypotenuse = ?":
        "sqrt(64 + 36) = sqrt(100) = 10. This is just the 3-4-5 triple scaled up by 2: (6,8,10). Scaling any Pythagorean triple gives another one.",
    "A right triangle has legs 7 and 24. Hypotenuse = ?":
        "sqrt(49 + 576) = sqrt(625) = 25. The 7-24-25 triple is less common but good to know. 625 = 5^4, so the hypotenuse is 5 squared.",
    "A right triangle has legs 9 and 12. Hypotenuse = ?":
        "sqrt(81 + 144) = sqrt(225) = 15. This is the 3-4-5 triple scaled by 3: (9,12,15). Scaling preserves the right angle.",
    "Pythagorean theorem: a^2 + b^2 = ___?":
        "a^2 + b^2 = c^2, where c is the hypotenuse. This 2,500-year-old theorem connects the sides of every right triangle and is the foundation of distance calculations.",

    # ===== TIER 4: Two-step algebra =====
    "If 2x + 5 = 17, then x = ?":
        "Subtract 5: 2x = 12. Divide by 2: x = 6. Two-step equations undo operations in reverse order -- subtraction first, then division.",
    "If 3x - 4 = 14, then x = ?":
        "Add 4: 3x = 18. Divide by 3: x = 6. Work backwards: undo the subtraction, then undo the multiplication.",
    "If 4x + 3 = 23, then x = ?":
        "Subtract 3: 4x = 20. Divide by 4: x = 5. Each step peels away one layer of the equation.",
    "If 5x - 10 = 25, then x = ?":
        "Add 10: 5x = 35. Divide by 5: x = 7. Adding first eliminates the constant, then dividing isolates x.",
    "If 2x + 9 = 25, then x = ?":
        "Subtract 9: 2x = 16. Divide by 2: x = 8. Each inverse operation brings you one step closer to the answer.",
    "If 6x - 6 = 30, then x = ?":
        "Add 6: 6x = 36. Divide by 6: x = 6. Beautifully symmetric -- 6 appears as the coefficient, constant, and answer.",
    "If 3x + 7 = 28, then x = ?":
        "Subtract 7: 3x = 21. Divide by 3: x = 7. Blackjack math: 3 x 7 = 21.",
    "If 10x - 5 = 45, then x = ?":
        "Add 5: 10x = 50. Divide by 10: x = 5. Dividing by 10 is easy -- just drop the zero.",
    "If 2x - 3 = 11, then x = ?":
        "Add 3: 2x = 14. Divide by 2: x = 7. Undo subtraction with addition, undo multiplication with division.",
    "If 4x + 8 = 32, then x = ?":
        "Subtract 8: 4x = 24. Divide by 4: x = 6. Each step simplifies until x stands alone.",

    # ===== TIER 4: Negative numbers =====
    "-8 + 5 = ?":
        "-8 + 5 = -3. Start at -8 on the number line and move 5 to the right. You end up at -3, still on the negative side.",
    "-4 + (-6) = ?":
        "-4 + (-6) = -10. Adding two negatives pushes further left on the number line. Think of it as owing $4 plus owing $6 -- you owe $10.",
    "7 - 12 = ?":
        "7 - 12 = -5. When you subtract a larger number from a smaller one, you cross zero into negative territory.",
    "-9 - 3 = ?":
        "-9 - 3 = -12. Starting negative and subtracting more pushes further into debt. Think: -9 and then 3 more steps left.",
    "-6 x -4 = ?":
        "-6 x -4 = 24. Negative times negative equals positive. Think of it as reversing a reversal -- two negatives cancel out.",
    "-5 x 3 = ?":
        "-5 x 3 = -15. Negative times positive is negative. Three groups of -5 debt gives -15 total debt.",
    "(-3)^2 = ?":
        "(-3)^2 = 9. Squaring any number, positive or negative, gives a positive result because negative times negative is positive.",
    "-24 / 6 = ?":
        "-24 / 6 = -4. Negative divided by positive is negative. Think: sharing $24 of debt among 6 people means each owes $4.",
    "-36 / -9 = ?":
        "-36 / -9 = 4. Negative divided by negative is positive. The two negatives cancel, just like in multiplication.",
    "-7 x -7 = ?":
        "-7 x -7 = 49. Squaring -7 gives the same result as squaring 7. Every squared number is non-negative.",

    # ===== TIER 4: Fractions =====
    "1/2 + 1/4 = ?":
        "1/2 + 1/4 = 3/4. Convert 1/2 to 2/4, then add: 2/4 + 1/4 = 3/4. Finding a common denominator is the key to adding fractions.",
    "What is the sum of the interior angles of a pentagon?":
        "A pentagon has interior angles summing to 540 degrees. The formula is (n-2) x 180, so (5-2) x 180 = 3 x 180 = 540. Each additional side adds another 180 degrees.",
    "3/4 - 1/4 = ?":
        "3/4 - 1/4 = 2/4 = 1/2. Same denominator, so just subtract the numerators: 3 - 1 = 2. Then simplify 2/4 to 1/2.",
    "If a triangle has angles of 45 and 60 degrees, what is the third angle?":
        "180 - 45 - 60 = 75 degrees. All triangle angles sum to 180 degrees, a fact proven by the ancient Greeks. The third angle fills the gap.",
    "1/2 - 1/4 = ?":
        "1/2 - 1/4 = 1/4. Convert 1/2 to 2/4, then subtract: 2/4 - 1/4 = 1/4. Half minus a quarter leaves a quarter.",

    # ===== TIER 4: Powers =====
    "2^3 = ?":
        "2 cubed is 8. That's 2 x 2 x 2. Eight bits make a byte in computing, and 2^3 is the foundation of binary representation.",
    "3^3 = ?":
        "3 cubed is 27. A Rubik's cube is 3 x 3 x 3 = 27 smaller cubes. Cubing a number means using it as a factor three times.",
    "What is 2^4?":
        "2 to the 4th is 16. That's 2 x 2 x 2 x 2. There are 16 ounces in a pound and 16 values in a single hexadecimal digit.",
    "3^4 = ?":
        "3 to the 4th is 81, or 3 x 3 x 3 x 3. Notice that 3^4 = (3^2)^2 = 9^2 = 81. Stacking exponents is just repeated squaring.",
    "What is 2^5?":
        "2 to the 5th is 32. That's 2 x 2 x 2 x 2 x 2. There are 32 teams in the NFL and 32 teeth in a full adult set.",
    "4^3 = ?":
        "4 cubed is 64. That's 4 x 4 x 4, or equivalently 2^6. A chess board has 64 squares, connecting geometry and powers.",
    "5^3 = ?":
        "5 cubed is 125. That's 5 x 5 x 5. In the metric system, a cube with 5 cm sides holds 125 cubic centimeters.",
    "What is 2^6?":
        "2 to the 6th is 64. That's the same as 4^3 or 8^2. The number 64 appears constantly in computing -- 64-bit processors, N64, etc.",
    "10^3 = ?":
        "10 cubed is 1000. The prefix 'kilo' means 1000 -- a kilogram, a kilometer, a kilobyte. Powers of 10 define our measurement system.",
    "If 7x + 2 = 30, then x = ?":
        "Subtract 2: 7x = 28. Divide by 7: x = 4. Two inverse operations in sequence isolate x.",
    "If 9x - 9 = 54, then x = ?":
        "Add 9: 9x = 63. Divide by 9: x = 7. Factor out 9 and you see 9(x - 1) = 54, so x - 1 = 6, x = 7.",
    "-2 + 15 = ?":
        "-2 + 15 = 13. Start at -2 and move 15 to the right on the number line. You pass through zero and land on 13.",
    "20 + (-8) = ?":
        "20 + (-8) = 12. Adding a negative is the same as subtracting: 20 - 8 = 12. A dozen remains.",
    "A right triangle has legs 20 and 21. Hypotenuse = ?":
        "sqrt(400 + 441) = sqrt(841) = 29. The 20-21-29 triple is a primitive Pythagorean triple -- not a scaled-up version of anything simpler.",
    "If 2x + 1 = 15, then x = ?":
        "Subtract 1: 2x = 14. Divide by 2: x = 7. Two quick steps to isolate x, just like peeling layers off an onion.",
    "3/4 + 1/4 = ?":
        "3/4 + 1/4 = 4/4 = 1. When fractions share a denominator, just add the numerators. Four quarters make a whole.",
    "-3 x 8 = ?":
        "-3 x 8 = -24. Negative times positive is negative. Three debts of $8 each total $24 of debt.",
    "(-2)^3 = ?":
        "(-2)^3 = -8. An odd exponent preserves the negative sign: (-2) x (-2) x (-2) = 4 x (-2) = -8.",
    "Surface area of a cube with side 5 = ?":
        "SA = 6 x 5^2 = 6 x 25 = 150 square units. Six faces, each 25 square units. Surface area scales with the square of the side.",
    "If 11x - 11 = 44, then x = ?":
        "Add 11: 11x = 55. Divide by 11: x = 5. Factor out 11: 11(x-1) = 44, so x - 1 = 4, x = 5.",

    # ===== TIER 5: Trigonometry =====
    "sin(30 deg) = ?":
        "sin(30) = 1/2. In a 30-60-90 triangle, the side opposite 30 degrees is half the hypotenuse. This is one of the most important trig values to memorize.",
    "sin(90 deg) = ?":
        "sin(90) = 1. At 90 degrees, a point on the unit circle reaches its maximum height of 1. The sine function peaks here.",
    "sin(0 deg) = ?":
        "sin(0) = 0. At 0 degrees, a point on the unit circle is at (1,0) -- no vertical component. Sine measures the y-coordinate on the unit circle.",
    "sin(45 deg) = ?":
        "sin(45) = sqrt(2)/2, about 0.707. A 45-45-90 triangle is isosceles, so sine and cosine are equal. This value appears everywhere in physics and engineering.",
    "sin(60 deg) = ?":
        "sin(60) = sqrt(3)/2, about 0.866. In a 30-60-90 triangle, the side opposite 60 degrees is sqrt(3)/2 times the hypotenuse.",
    "cos(90 deg) = ?":
        "cos(90) = 0. At 90 degrees on the unit circle, the x-coordinate is zero. Cosine and sine are complementary: cos(90) = sin(0) = 0.",
    "cos(60 deg) = ?":
        "cos(60) = 1/2. Cosine at 60 equals sine at 30 because they're complementary angles (60 + 30 = 90). The word 'cosine' literally means 'complement's sine.'",
    "cos(30 deg) = ?":
        "cos(30) = sqrt(3)/2, about 0.866. Same as sin(60), because cosine and sine are complementary. A 30-60-90 triangle encodes both values.",
    "cos(45 deg) = ?":
        "cos(45) = sqrt(2)/2. At 45 degrees, sine and cosine are equal because the triangle is isosceles. This is the balance point of the trig functions.",
    "tan(0 deg) = ?":
        "tan(0) = 0. Tangent = sin/cos = 0/1 = 0. At 0 degrees, there is no vertical rise, so the tangent (slope) is zero.",
    "tan(45 deg) = ?":
        "tan(45) = 1. Since sin(45) = cos(45), their ratio is 1. A 45-degree line has a slope of exactly 1 -- it rises as fast as it runs.",
    "tan(60 deg) = ?":
        "tan(60) = sqrt(3), about 1.732. It's sin(60)/cos(60) = (sqrt(3)/2) / (1/2) = sqrt(3). A steep incline!",
    "tan(30 deg) = ?":
        "tan(30) = 1/sqrt(3), or equivalently sqrt(3)/3. It's the reciprocal of tan(60). A gentle 30-degree slope rises slowly.",

    # ===== TIER 5: Logarithms =====
    "log10(100) = ?":
        "log10(100) = 2 because 10^2 = 100. Logarithms ask: 'What power gives this result?' The Richter scale uses log base 10, so each step is 10x stronger.",
    "log10(1000) = ?":
        "log10(1000) = 3 because 10^3 = 1000. The prefix 'kilo' means 10^3. Logarithms turn multiplication into addition, which is why they revolutionized computation.",
    "log10(10) = ?":
        "log10(10) = 1 because 10^1 = 10. The log of the base itself is always 1. This is the simplest logarithm fact.",
    "log10(1) = ?":
        "log10(1) = 0 because 10^0 = 1. Any base raised to the zero power equals 1, so the log of 1 is always 0, regardless of base.",
    "log2(8) = ?":
        "log2(8) = 3 because 2^3 = 8. In computing, 3 bits can represent 8 different values (0 through 7).",
    "log2(16) = ?":
        "log2(16) = 4 because 2^4 = 16. Four bits represent 16 values, which is why hexadecimal (base 16) uses 4 binary digits.",
    "log2(4) = ?":
        "log2(4) = 2 because 2^2 = 4. Two bits give 4 possible states: 00, 01, 10, 11. This is the foundation of binary encoding.",
    "log2(32) = ?":
        "log2(32) = 5 because 2^5 = 32. Five bits represent 32 values, enough for all 26 letters of the alphabet plus a few extras.",
    "log2(1) = ?":
        "log2(1) = 0 because 2^0 = 1. The log of 1 is always 0 in any base, since any number to the zero power is 1.",

    # ===== TIER 5: Quadratic formula =====
    "The discriminant of ax^2 + bx + c = 0 is ___?":
        "The discriminant is b^2 - 4ac. It determines the nature of the roots: positive means two real roots, zero means one, negative means complex. It's the part under the square root in the quadratic formula.",
    "In the quadratic formula, the denominator is ___?":
        "The denominator is 2a. The full formula is x = (-b +/- sqrt(b^2 - 4ac)) / 2a. The 2a comes from completing the square on ax^2 + bx + c.",
    "The quadratic formula gives x = (-b +/- sqrtD) / ___?":
        "The denominator is 2a. This formula solves any quadratic equation ax^2 + bx + c = 0, even when factoring isn't possible.",
    "If discriminant > 0, the quadratic has ___ real roots?":
        "Two real roots. A positive discriminant means the square root is a real number, and the +/- gives two distinct solutions.",
    "If discriminant = 0, the quadratic has ___ real root(s)?":
        "Exactly 1 real root (a repeated root). When the discriminant is zero, +/- sqrt(0) adds nothing, so both branches give the same answer.",

    # ===== TIER 5: Distance and slope =====
    "Distance between (0,0) and (3,4) = ?":
        "sqrt(9 + 16) = sqrt(25) = 5. The distance formula is the Pythagorean theorem in disguise: the horizontal and vertical legs form a right triangle.",
    "Distance between (0,0) and (5,12) = ?":
        "sqrt(25 + 144) = sqrt(169) = 13. Another Pythagorean triple (5,12,13) makes this distance a clean integer.",
    "Distance formula = sqrt((x2-x1)^2 + ___^2)?":
        "The missing term is (y2-y1). The distance formula comes from the Pythagorean theorem applied to the horizontal and vertical differences between two points.",
    "Slope of a line through (0,0) and (4,8) = ?":
        "Slope = (8-0)/(4-0) = 8/4 = 2. The line rises 2 units for every 1 unit it runs. Slope measures steepness as rise over run.",
    "Slope of a line through (1,2) and (3,6) = ?":
        "Slope = (6-2)/(3-1) = 4/2 = 2. Same slope as the origin-to-(4,8) line -- parallel lines share the same slope.",
    "Slope of a line through (0,5) and (5,0) = ?":
        "Slope = (0-5)/(5-0) = -5/5 = -1. A negative slope means the line falls from left to right. This line makes a 135-degree angle with the x-axis.",
    "Slope formula = (y2 - y1) / ___?":
        "Slope = (y2 - y1) / (x2 - x1). Rise over run. The vertical change divided by the horizontal change gives the steepness of the line.",
    "Slope of a horizontal line = ?":
        "Zero. A horizontal line has no rise, so rise/run = 0/run = 0. Think of a flat road -- zero incline, zero slope.",
    "Slope of a vertical line = ?":
        "Undefined. A vertical line has no run, so rise/run = rise/0, which is division by zero. Vertical lines are infinitely steep.",

    # ===== TIER 5: Statistics =====
    "Mean of 4, 7, 9, 12, 8 = ?":
        "Mean = (4+7+9+12+8)/5 = 40/5 = 8. The mean (average) balances all values. Think of it as redistributing the total equally among all data points.",
    "Mean of 2, 4, 6, 8, 10 = ?":
        "Mean = 30/5 = 6. For evenly spaced numbers, the mean is the middle value. The arithmetic mean of an arithmetic sequence is always the middle term.",
    "Median of 3, 5, 7, 9, 11 = ?":
        "The median is 7, the middle value when data is sorted. The median isn't affected by extreme values, making it more robust than the mean.",
    "Median of 1, 3, 5, 9, 12 = ?":
        "The median is 5, the middle value of the sorted list. Even though 9 and 12 are large, they don't pull the median upward.",
    "Mode of 2, 3, 3, 4, 5 = ?":
        "The mode is 3, since it appears twice while all others appear once. The mode is the only measure of central tendency that works for non-numeric data too.",
    "Mode of 1, 2, 2, 3, 4, 4, 4 = ?":
        "The mode is 4, appearing three times -- more than any other value. A dataset can have multiple modes if there's a tie.",
    "Range of 3, 7, 2, 9, 5 = ?":
        "Range = max - min = 9 - 2 = 7. The range measures the spread of data. It's simple but sensitive to outliers.",
    "Mean of 10, 20, 30 = ?":
        "Mean = 60/3 = 20. For three evenly spaced numbers, the mean is always the middle number. Simple and symmetric.",

    # ===== TIER 5: Negative exponents =====
    "2^(-1) = ?":
        "2^(-1) = 1/2. A negative exponent means 'take the reciprocal.' So 2^(-1) flips 2 into 1/2.",
    "2^(-2) = ?":
        "2^(-2) = 1/4. That's 1/(2^2) = 1/4. Negative exponents flip the base and then apply the positive exponent.",
    "10^(-1) = ?":
        "10^(-1) = 0.1. One-tenth. Moving the decimal point one place left is the same as dividing by 10, which is 10^(-1).",
    "10^(-2) = ?":
        "10^(-2) = 0.01. One-hundredth. Each negative power of 10 moves the decimal one more place to the left.",

    # ===== TIER 5: Fraction square roots =====
    "sqrt(49/64) = ?":
        "sqrt(49/64) = 7/8. The square root distributes over fractions: sqrt(49)/sqrt(64) = 7/8. Each part simplifies independently.",
    "sqrt(9/16) = ?":
        "sqrt(9/16) = 3/4. Take the square root of the numerator and denominator separately: sqrt(9) = 3, sqrt(16) = 4.",

    # ===== TIER 5: Function evaluation =====
    "If f(x) = 2x + 3, then f(5) = ?":
        "f(5) = 2(5) + 3 = 10 + 3 = 13. Plug in the input, compute the output. Functions are like machines -- put in 5, get out 13.",
    "If f(x) = x^2 - 1, then f(4) = ?":
        "f(4) = 16 - 1 = 15. Square the input, subtract 1. This function shifts the parabola down by 1 unit.",
    "If f(x) = 3x - 2, then f(6) = ?":
        "f(6) = 18 - 2 = 16. A linear function with slope 3 and y-intercept -2. Every increase of 1 in x adds 3 to the output.",
    "If f(x) = x^2 + 2x, then f(3) = ?":
        "f(3) = 9 + 6 = 15. Factor it: x(x+2) = 3 x 5 = 15. Factoring can make evaluation faster than expanding.",
    "Distance between (1,1) and (4,5) = ?":
        "sqrt((3)^2 + (4)^2) = sqrt(9+16) = sqrt(25) = 5. It's a 3-4-5 triangle hiding in the coordinate plane!",
    "Slope of a line through (2,3) and (4,7) = ?":
        "Slope = (7-3)/(4-2) = 4/2 = 2. Rise of 4 over run of 2 gives a slope of 2. The line goes up 2 units for every 1 unit right.",
    "Mean of 5, 5, 5, 5, 5 = ?":
        "Mean = 25/5 = 5. When all values are equal, the mean is that value. Zero variation means the average IS every data point.",
    "Median of 2, 4, 6, 8, 10 = ?":
        "The median is 6, the middle of five sorted values. For this evenly spaced set, the mean and median are both 6.",
    "log10(10000) = ?":
        "log10(10000) = 4 because 10^4 = 10000. The number of zeros in a power of 10 equals its base-10 logarithm.",
    "What is 2^0?":
        "2^0 = 1. Any nonzero number raised to the power 0 equals 1. Think of it as: each time you decrease the exponent by 1, you divide by the base. 2^1 = 2, so 2^0 = 2/2 = 1.",
    "Any nonzero number raised to the power 0 = ?":
        "The answer is 1. This follows from the exponent rule: a^n / a^n = a^(n-n) = a^0. Since anything divided by itself is 1, a^0 = 1.",
    "log2(64) = ?":
        "log2(64) = 6 because 2^6 = 64. A 64-bit system uses 6 binary doublings from 1. Nintendo named a console after this number.",
    "If f(x) = x^2 + 1, then f(0) = ?":
        "f(0) = 0 + 1 = 1. Zero squared is zero, plus one gives 1. This is the y-intercept of the parabola y = x^2 + 1.",
    "The y-intercept of y = 3x + 7 is ___?":
        "The y-intercept is 7. In y = mx + b form, b is where the line crosses the y-axis (when x = 0). Plugging in x = 0 gives y = 7.",
    "The slope of y = 5x - 2 is ___?":
        "The slope is 5. In y = mx + b form, m is the slope. This line rises 5 units for every 1 unit to the right -- quite steep!",
    "tan(90 deg) = ?":
        "tan(90) is undefined. Since cos(90) = 0, tan(90) = sin(90)/cos(90) = 1/0, which is division by zero. The tangent function has a vertical asymptote here.",
    "sin^2(theta) + cos^2(theta) = ?":
        "Always 1. This is the Pythagorean identity, derived from x^2 + y^2 = 1 on the unit circle. It holds for every angle, no exceptions.",
    "Distance between (0,0) and (8,6) = ?":
        "sqrt(64 + 36) = sqrt(100) = 10. The 6-8-10 triple is the 3-4-5 triple doubled. Recognizing scaled triples saves computation time.",
    "Range of 10, 4, 7, 2, 9 = ?":
        "Range = 10 - 2 = 8. Max minus min. The range captures the total spread of the data but ignores everything in between.",

    # ===== Additional TIER 1 =====
    "4 x 3 = ?":
        "4 x 3 = 12. Three groups of four, or four groups of three -- multiplication is commutative. There are 12 eggs in a carton and 12 notes in an octave.",
    "5 x 4 = ?":
        "5 x 4 = 20. A nickel (5 cents) times 4 gives 20 cents. Multiplying by 5 is halving and appending a 0: half of 4 is 2, so 20.",

    # ===== Additional TIER 2 =====
    "25% of 200 = ?":
        "25% of 200 = 50. One quarter of 200 is 50. Halve 200 to get 100, halve again to get 50.",
    "1/2 of 98 = ?":
        "Half of 98 is 49. Halve 100 to get 50, subtract 1 because 98 is 2 less than 100. Or: 98/2 = 49, which is also 7 squared.",
    "10% of 90 = ?":
        "10% of 90 = 9. Move the decimal one place left. Nine is also the digit sum of 90, a happy coincidence for this particular problem.",

    # ===== Additional TIER 3 =====
    "Perimeter of a rectangle 4 x 11 = ?":
        "Perimeter = 2(4 + 11) = 2 x 15 = 30 units. Add the two different sides, then double. Perimeter measures the total boundary length.",
    "Area of a triangle: base=7, height=6 = ?":
        "Area = 1/2 x 7 x 6 = 21 square units. Half of 42 -- even the Answer to Everything gets halved by the triangle formula.",
    "sqrt0 = ?":
        "The square root of 0 is 0, because 0 x 0 = 0. Zero is the only number that is its own square root and also equals its own square.",
    "If 6x = 54, then x = ?":
        "Divide both sides by 6: x = 54/6 = 9. The finger trick for 6 x 9 = 54 works in reverse too.",
    "If x + 6 = 22, then x = ?":
        "Subtract 6 from both sides: x = 22 - 6 = 16. Sixteen is 2^4, a sweet power of two hiding in basic algebra.",
    "4 x 3 + 2 x 5 = ?":
        "Multiply first: 12 + 10 = 22. PEMDAS says both multiplications happen before the addition. Two products, one sum.",
    "Area of a square with side 12 = ?":
        "Area = 12 x 12 = 144 square units, a gross. The largest fact in the 12x12 table, and knowing it makes you a times-table master.",
    "Perimeter of a square with side 9 = ?":
        "Perimeter = 4 x 9 = 36 units. Four equal sides of 9. Notice the perimeter equals the area of a 6x6 square -- a coincidence, not a rule!",
    "Area of a rectangle 4 x 13 = ?":
        "Area = 4 x 13 = 52 square units. There are 52 cards in a standard deck and 52 weeks in a year.",
    "If 2x = 18, then x = ?":
        "Divide both sides by 2: x = 9. Half of 18 is 9. The simplest one-step equation -- just halve the right side.",
    "If x - 9 = 18, then x = ?":
        "Add 9 to both sides: x = 27. That's 3 cubed. Undoing subtraction with addition is the most basic algebraic move.",
    "(6 - 2) x (3 + 1) = ?":
        "Parentheses first: 4 x 4 = 16. Two parentheses reduce to a simple square: 4^2 = 16.",
    "3^2 + 4^2 = ?":
        "9 + 16 = 25 = 5^2. This is the Pythagorean theorem in action: 3^2 + 4^2 = 5^2. The most famous triple in mathematics.",
    "Area of a triangle: base=5, height=10 = ?":
        "Area = 1/2 x 5 x 10 = 25 square units. Half of 50. Also a perfect square (5^2), making this a pleasingly symmetric triangle.",
    "Perimeter of a rectangle 6 x 11 = ?":
        "Perimeter = 2(6 + 11) = 2 x 17 = 34 units. Add the sides, double the sum. Seventeen doubled is 34.",
    "If x / 3 = 12, then x = ?":
        "Multiply both sides by 3: x = 36. Three dozen is 36, and 36 is also 6 squared.",
    "5 + 2 x 6 - 1 = ?":
        "Multiply first: 5 + 12 - 1 = 16. PEMDAS says 2 x 6 = 12 happens first, then left-to-right: 5 + 12 = 17, 17 - 1 = 16.",
    "Area of a square with side 5 = ?":
        "Area = 5 x 5 = 25 square units. Five squared is a quarter of 100. A 5x5 grid is used in Bingo cards.",
    "Perimeter of a square with side 4 = ?":
        "Perimeter = 4 x 4 = 16 units. Four sides of four -- a square's perimeter equals its side length times 4.",
    "If 11x = 99, then x = ?":
        "Divide both sides by 11: x = 9. Eleven nines are 99, one short of 100.",
    "Area of a rectangle 9 x 11 = ?":
        "Area = 9 x 11 = 99 square units. One short of 100! Multiplying by 11: 9 x 10 + 9 = 90 + 9 = 99.",
    "2 x (4 + 3) - 5 = ?":
        "Parentheses first: 2 x 7 - 5 = 14 - 5 = 9. Evaluate parentheses, then multiply, then subtract -- strict PEMDAS order.",

    # ===== Additional TIER 4 =====
    "If 8x - 8 = 48, then x = ?":
        "Add 8: 8x = 56. Divide by 8: x = 7. Or factor: 8(x-1) = 48, so x-1 = 6, x = 7.",
    "If 5x + 5 = 40, then x = ?":
        "Subtract 5: 5x = 35. Divide by 5: x = 7. Or factor: 5(x+1) = 40, so x+1 = 8, x = 7.",
    "-15 / 3 = ?":
        "-15 / 3 = -5. Negative divided by positive gives negative. Think: splitting $15 of debt 3 ways means $5 debt each.",
    "8 x (-3) = ?":
        "8 x (-3) = -24. Positive times negative is negative. Eight groups of -3 debt total -24.",
    "(-4)^2 = ?":
        "(-4)^2 = 16. Squaring a negative gives a positive: (-4) x (-4) = 16. The negative cancels itself when the exponent is even.",
    "(-5)^3 = ?":
        "(-5)^3 = -125. Odd powers preserve the sign: (-5) x (-5) x (-5) = 25 x (-5) = -125. Odd exponent means negative result.",
    "1/4 + 1/4 = ?":
        "1/4 + 1/4 = 2/4 = 1/2. Same denominator, so add the numerators: 1 + 1 = 2. Two quarters make a half.",
    "3/4 + 1/2 = ?":
        "3/4 + 2/4 = 5/4 (or 1 and 1/4). Convert 1/2 to 2/4 first. The result exceeds 1 -- an improper fraction.",
    "Volume of a box 6 x 5 x 2 = ?":
        "6 x 5 x 2 = 60 cubic units. Start with 6 x 5 = 30, then 30 x 2 = 60. Same volume as a 3x4x5 box!",
    "Volume of a cube with side 6 = ?":
        "6^3 = 216 cubic units. Six cubed. This is also 6 x 6 x 6 = 36 x 6 = 216. In old English, 216 = 6^3 was called a 'cube of six.'",
    "Surface area of a cube with side 6 = ?":
        "SA = 6 x 6^2 = 6 x 36 = 216 square units. A rare coincidence: the surface area and volume of a cube with side 6 are both 216!",
    "A right triangle has legs 10 and 24. Hypotenuse = ?":
        "sqrt(100 + 576) = sqrt(676) = 26. This is the 5-12-13 triple doubled: (10, 24, 26). Scaling a Pythagorean triple always gives another valid triple.",
    "A right triangle has legs 15 and 20. Hypotenuse = ?":
        "sqrt(225 + 400) = sqrt(625) = 25. The 3-4-5 triple scaled by 5: (15, 20, 25). The hypotenuse is 5^3.",
    "What is 2^7?":
        "2^7 = 128. That's 2 x 64. ASCII uses 7 bits to represent 128 characters -- enough for all English letters, digits, and symbols.",
    "3^2 x 4 = ?":
        "Exponent first: 9 x 4 = 36. The exponent applies only to 3, not to 3 x 4. PEMDAS prevents misreading.",
    "If 3x + 12 = 33, then x = ?":
        "Subtract 12: 3x = 21. Divide by 3: x = 7. Blackjack number 21 divided by 3 gives lucky 7.",
    "If 4x - 12 = 20, then x = ?":
        "Add 12: 4x = 32. Divide by 4: x = 8. Thirty-two is 2^5, and dividing by 4 gives 8 = 2^3.",
    "-10 + (-10) = ?":
        "-10 + (-10) = -20. Two debts of $10 equal $20 of debt. Adding negatives is like accumulating more debt.",
    "-6 + 6 = ?":
        "-6 + 6 = 0. A number plus its opposite is always zero. This is the additive inverse property -- every number has a canceling partner.",
    "-3 x -3 x -3 = ?":
        "-3 x -3 x -3 = -27. First two negatives cancel: 9. Then 9 x (-3) = -27. An odd count of negatives gives a negative product.",
    "1/2 x 1/2 = ?":
        "1/2 x 1/2 = 1/4. Half of a half is a quarter. To multiply fractions, multiply numerators and denominators separately: 1x1=1, 2x2=4.",
    "2/3 x 3/4 = ?":
        "2/3 x 3/4 = 6/12 = 1/2. The 3s cancel: (2 x 3)/(3 x 4) simplifies to 2/4 = 1/2. Cross-cancellation makes fraction multiplication fast.",
    "Volume of a box 10 x 3 x 2 = ?":
        "10 x 3 x 2 = 60 cubic units. Start with 10 x 3 = 30, then double it. Same volume as a 6x5x2 box.",
    "If 12x + 6 = 54, then x = ?":
        "Subtract 6: 12x = 48. Divide by 12: x = 4. Or factor: 6(2x+1) = 54, so 2x+1 = 9, x = 4.",
    "If 2(x + 3) = 18, then x = ?":
        "Divide by 2: x + 3 = 9. Subtract 3: x = 6. Distributing first also works: 2x + 6 = 18, 2x = 12, x = 6.",
    "(-2)^4 = ?":
        "(-2)^4 = 16. Even exponents always produce positive results: (-2)^4 = (-2)^2 x (-2)^2 = 4 x 4 = 16.",
    "Surface area of a cube: formula = 6 x ___?":
        "Surface area = 6 x s^2. A cube has 6 identical square faces, each with area s^2. Multiply one face's area by 6 to wrap the whole cube.",
    "A right triangle has legs 6 and 8. Hypotenuse = ?":
        "sqrt(36 + 64) = sqrt(100) = 10. This is the 3-4-5 triple doubled. Recognizing scaled triples makes these problems instant.",
    "If 5x - 20 = 0, then x = ?":
        "Add 20: 5x = 20. Divide by 5: x = 4. Or factor: 5(x-4) = 0, so x = 4. Setting an expression equal to zero is the heart of equation solving.",
    "What is 2^8?":
        "2^8 = 256. This is the number of values a single byte can hold (0-255). Computer graphics use 256 levels per color channel.",
    "-4 x -4 x 4 = ?":
        "(-4) x (-4) x 4 = 16 x 4 = 64. The first two negatives cancel to give 16, then 16 x 4 = 64. Even count of negatives means positive.",
    "If 6x + 6 = 42, then x = ?":
        "Subtract 6: 6x = 36. Divide by 6: x = 6. Or factor: 6(x+1) = 42, so x+1 = 7, x = 6. Beautifully symmetric.",
    "Volume of a cube with side 1 = ?":
        "1^3 = 1 cubic unit. The unit cube is the building block of all volume measurements. Every other cube volume is measured in multiples of this one.",

    # ===== Additional TIER 5 =====
    "Mean of 1, 3, 5, 7, 9 = ?":
        "Mean = 25/5 = 5. For an arithmetic sequence, the mean equals the middle term. The odd numbers 1-9 average to the center value.",
    "Median of 4, 4, 7, 10, 10 = ?":
        "The median is 7, the middle value. Even though 4 and 10 each appear twice, the median picks the single center value.",
    "Mode of 5, 6, 6, 7, 8, 8, 8 = ?":
        "The mode is 8, appearing three times. Mode means 'most frequent.' Even though 6 appears twice, 8 wins with three appearances.",
    "Range of 15, 3, 9, 21, 6 = ?":
        "Range = 21 - 3 = 18. The biggest minus the smallest. This tells you the total spread of the data at a glance.",
    "log10(0.1) = ?":
        "log10(0.1) = -1 because 10^(-1) = 0.1. Negative logs correspond to numbers between 0 and 1. Each step below 0 moves the decimal one place left.",
    "log2(1/2) = ?":
        "log2(1/2) = -1 because 2^(-1) = 1/2. Halving is the inverse of doubling, and the log reflects that as -1.",
    "sin^2(30 deg) + cos^2(30 deg) = ?":
        "Always 1. The Pythagorean identity sin^2 + cos^2 = 1 holds for every angle. Here: (1/2)^2 + (sqrt3/2)^2 = 1/4 + 3/4 = 1.",
    "If f(x) = x^3, then f(3) = ?":
        "f(3) = 27. Three cubed is 27 -- the volume of a 3x3x3 Rubik's cube. Cubic functions grow much faster than quadratic ones.",
    "If f(x) = sqrtx, then f(49) = ?":
        "f(49) = 7. The square root function asks: what number squared gives 49? Since 7 x 7 = 49, the answer is 7.",
    "If f(x) = x^2 - 4, then f(3) = ?":
        "f(3) = 9 - 4 = 5. This function can also be factored: (x-2)(x+2) = (1)(5) = 5. Factored form sometimes makes evaluation easier.",
    "Slope of y = -3x + 1 is ___?":
        "The slope is -3. In y = mx + b, the coefficient of x is the slope. Negative slope means the line falls from left to right.",
    "y-intercept of y = 2x - 5 is ___?":
        "The y-intercept is -5. That's where the line crosses the y-axis (at x = 0). In y = mx + b, b is always the y-intercept.",
    "Distance between (0,0) and (6,8) = ?":
        "sqrt(36 + 64) = sqrt(100) = 10. Another 3-4-5 triple in disguise (doubled). The distance formula is just Pythagoras on the coordinate plane.",
    "Distance between (1,2) and (4,6) = ?":
        "sqrt(9 + 16) = sqrt(25) = 5. Differences: 4-1=3 and 6-2=4, giving the classic 3-4-5 right triangle.",
    "Slope of a line through (3,3) and (6,9) = ?":
        "Slope = (9-3)/(6-3) = 6/3 = 2. Rise of 6 over run of 3. This line passes through the origin too (y = 2x).",
    "3^(-1) = ?":
        "3^(-1) = 1/3. A negative exponent means 'take the reciprocal.' Flipping 3 gives one-third.",
    "4^(-1) = ?":
        "4^(-1) = 1/4, or 0.25. The reciprocal of 4 is a quarter. Negative exponents always flip the base.",
    "5^0 = ?":
        "5^0 = 1. Any nonzero number to the zero power is 1. The pattern: 5^3=125, 5^2=25, 5^1=5 -- each time you divide by 5, so 5^0 = 5/5 = 1.",
    "log3(9) = ?":
        "log3(9) = 2 because 3^2 = 9. The logarithm asks: what power of 3 gives 9? The answer is 2.",
    "log3(27) = ?":
        "log3(27) = 3 because 3^3 = 27. A Rubik's cube has 27 small cubes, and it takes exactly 3 doublings of base-3 to reach it.",
    "The quadratic formula: x = ?":
        "x = (-b +/- sqrt(b^2-4ac)) / 2a. This formula solves any quadratic ax^2+bx+c=0. It was known to ancient Babylonian and Indian mathematicians millennia ago.",
    "If discriminant < 0, the quadratic has ___ real roots?":
        "Zero real roots. A negative discriminant means you'd need the square root of a negative number, which isn't real. The roots are complex (involving i).",
    "The reciprocal of sin(theta) is ___?":
        "csc(theta), the cosecant. It's 1/sin(theta). The 'co-' prefix in trig doesn't mean complement here -- cosecant is simply the reciprocal of sine.",
    "The reciprocal of cos(theta) is ___?":
        "sec(theta), the secant. It's 1/cos(theta). Secant comes from the Latin 'secare' (to cut), describing how it cuts across a circle.",
    "Mean of 0, 0, 10, 10, 10 = ?":
        "Mean = 30/5 = 6. The mean gets pulled toward the cluster of 10s. This shows how the mean balances zeros and nonzero values.",
    "Median of 1, 2, 3, 100, 200 = ?":
        "The median is 3. Unlike the mean (which would be 61.2), the median isn't affected by the extreme values 100 and 200. It's robust to outliers.",
    "log10(0.01) = ?":
        "log10(0.01) = -2 because 10^(-2) = 0.01. Each negative step divides by 10 again. The pattern: log(1)=0, log(0.1)=-1, log(0.01)=-2.",

    # ===== Additional TIER 3 =====
    "Area of a square with side 3 = ?":
        "Area = 3 x 3 = 9 square units. A 3x3 grid like tic-tac-toe has exactly 9 cells. The smallest non-trivial perfect square.",
    "Perimeter of a square with side 5 = ?":
        "Perimeter = 4 x 5 = 20 units. Four sides of five. A square's perimeter is always 4 times its side length.",

    # ===== Additional TIER 4 =====
    "If 3(x - 2) = 15, then x = ?":
        "Divide by 3: x - 2 = 5. Add 2: x = 7. You can also distribute first: 3x - 6 = 15, 3x = 21, x = 7.",

    # ===== Conceptual questions =====
    "What property says a + b = b + a?":
        "The commutative property says the order of addition doesn't matter. It works for multiplication too (a x b = b x a), but NOT for subtraction or division.",
    "What property says (a + b) + c = a + (b + c)?":
        "The associative property says grouping doesn't matter when adding. You can rearrange the parentheses freely. It also applies to multiplication.",
    "What is the value of zero added to any number?":
        "The number itself. Zero is the additive identity -- it leaves every number unchanged. In algebra, this property is used constantly to simplify expressions.",
    "What is any number multiplied by zero?":
        "Zero. No matter how large or small the number, multiplying by zero annihilates it. This is the zero product property.",
    "What is any nonzero number divided by itself?":
        "The answer is 1. Any number divided by itself gives 1, the multiplicative identity. This is why a/a = 1 for all a except 0.",
    "Is the sum of two even numbers always even, odd, or neither?":
        "Always even. Even + even = even because both contribute complete pairs. Think: 4 + 6 = 10, all even.",
    "Is the sum of two odd numbers always even or odd?":
        "Always even. Each odd number has a leftover 1, and two leftover 1s make a pair. Example: 3 + 5 = 8.",
    "Which is larger: 3/4 or 2/3?":
        "3/4 is larger. Convert to common denominator: 9/12 vs 8/12. Three-quarters is 75% while two-thirds is about 66.7%.",
    "What is the next prime number after 7?":
        "11. The number 8 is divisible by 2, 9 by 3, and 10 by 2 and 5. Eleven has no divisors except 1 and itself, making it prime.",
    "How many sides does a hexagon have?":
        "Six. The prefix 'hex' means six (as in hexadecimal). Honeycombs use hexagons because they tile a plane with no wasted space.",
    "25% of 60 = ?":
        "25% of 60 = 15. One-quarter of 60: halve to get 30, halve again to get 15. A quarter-hour is 15 minutes for exactly this reason.",
    "20% of 150 = ?":
        "20% of 150 = 30. Find 10% (15) and double it: 30. Twenty percent is one-fifth, so 150/5 = 30 also works.",
    "What is 15% of 200?":
        "15% of 200 = 30. Think: 10% is 20, plus 5% is 10, total 30. Breaking percentages into 10% and 5% chunks makes mental math fast.",
    "A number is divisible by 9 if the sum of its digits is divisible by ___?":
        "Divisible by 9. For example, 738: 7+3+8 = 18, and 18/9 = 2, so 738 is divisible by 9. This digit-sum test has been known since ancient India.",
    "A number is divisible by 3 if the sum of its digits is divisible by ___?":
        "Divisible by 3. For example, 123: 1+2+3 = 6, and 6/3 = 2. This trick works because 10 leaves remainder 1 when divided by 3.",
    "What makes a number even?":
        "A number is even if it's divisible by 2. It ends in 0, 2, 4, 6, or 8. Ending in 0 alone isn't enough -- 12, 34, 56 are all even too.",
    "What is a prime number?":
        "A number with exactly two factors: 1 and itself. This excludes 1 (only one factor) and includes 2 (the only even prime). Primes are the atoms of multiplication.",
    "What is the least common multiple of 4 and 6?":
        "LCM(4, 6) = 12. The smallest number both 4 and 6 divide into evenly. List multiples: 4,8,12... and 6,12... -- 12 is the first overlap.",
    "What is the greatest common factor of 12 and 18?":
        "GCF(12, 18) = 6. The largest number dividing both. Factors of 12: 1,2,3,4,6,12. Factors of 18: 1,2,3,6,9,18. The biggest overlap is 6.",
    "What is the reciprocal of 4?":
        "The reciprocal of 4 is 1/4. A number times its reciprocal always equals 1: 4 x 1/4 = 1. Reciprocals 'undo' multiplication.",
    "If you double a number and get 30, what is the number?":
        "15. Doubling means multiplying by 2, so undoing it means dividing by 2: 30/2 = 15. Working backwards is the essence of algebra.",
    "What does PEMDAS (or BODMAS) stand for in math?":
        "The order of operations: Parentheses, Exponents, Multiplication/Division, Addition/Subtraction. Without this convention, 2 + 3 x 4 could mean 14 or 20.",
    "What is the perimeter of an equilateral triangle with side 8?":
        "Perimeter = 3 x 8 = 24. An equilateral triangle has three equal sides. 'Equilateral' comes from Latin: equal (equi) sides (lateral).",
    "A square has area 64. What is its side length?":
        "Side = sqrt(64) = 8. Finding the side from the area is the inverse of squaring -- it's taking a square root. A chess board is 8 x 8.",
    "What is the sum of interior angles of any triangle?":
        "180 degrees. This holds for every triangle, no exceptions. You can verify by tearing off a triangle's corners and arranging them -- they form a straight line.",
    "What is the sum of interior angles of a quadrilateral?":
        "360 degrees. A quadrilateral can be split into two triangles: 2 x 180 = 360. The formula (n-2) x 180 works for any polygon.",
    "An isosceles triangle has two angles of 70 degrees. What is the third angle?":
        "180 - 70 - 70 = 40 degrees. An isosceles triangle has two equal angles. The third angle fills whatever's left to reach 180.",
    "What does a negative exponent mean? For example, what is x^(-n)?":
        "x^(-n) = 1/x^n. A negative exponent means 'flip to the denominator.' It's the reciprocal of the positive power.",
    "What is a^0 for any nonzero a?":
        "a^0 = 1. The pattern a^3, a^2, a^1 divides by a each step, so a^0 = a^1/a = 1. Zero is not allowed as a base here because 0^0 is debated.",
    "If f(x) = x + 3, what is f(7)?":
        "f(7) = 7 + 3 = 10. Substitute 7 for x and compute. Functions are input-output machines -- feed in 7, get out 10.",
    "What does the absolute value |x| represent?":
        "The distance from x to zero on the number line. It strips the sign: |5| = 5 and |-5| = 5. Distance is always non-negative.",
    "Which number is NOT prime: 11, 17, 21, 23?":
        "21 is not prime because 21 = 3 x 7. The other three (11, 17, 23) have no divisors other than 1 and themselves.",
    "What is the formula for the area of a circle with radius r?":
        "Area = pi x r^2. The area grows with the square of the radius -- double the radius and the area quadruples. Archimedes proved this around 250 BC.",
    "A line with slope 0 is ___?":
        "Horizontal. Zero slope means zero rise -- the line runs perfectly flat. Think of a calm lake surface.",
    "Two lines are parallel if they have ___ slopes?":
        "Equal slopes. Parallel lines never meet because they rise at the same rate. In y = mx + b form, same m means parallel.",
    "Two lines are perpendicular if the product of their slopes is ___?":
        "The product is -1. Their slopes are negative reciprocals: if one has slope 2, the other has slope -1/2. They form a 90-degree angle.",
    "What is log(a) + log(b) equal to, using the same base?":
        "log(a x b). Logarithms convert multiplication into addition. This property made slide rules possible and revolutionized pre-calculator computation.",
    "What is log(a) - log(b) equal to, using the same base?":
        "log(a/b). Logarithms convert division into subtraction. Combined with the addition rule, logs turn complex arithmetic into simple sums.",
    "What is n * log(a) equal to?":
        "log(a^n). The power rule pulls exponents out front. This is why logarithmic scales compress huge ranges -- exponents become simple multipliers.",
    "What does it mean for two fractions to have a common denominator?":
        "Their bottom numbers (denominators) are equal. You need a common denominator to add or subtract fractions. It's like converting to the same unit before combining.",
    "In the expression a^m * a^n, what is the simplified exponent?":
        "m + n. When multiplying powers with the same base, add the exponents: a^m x a^n = a^(m+n). This is the product rule for exponents.",
    "What does it mean for a function to be one-to-one?":
        "Each output corresponds to exactly one input. No two different inputs produce the same output. Graphically, it passes the horizontal line test.",
    "What is the geometric meaning of the derivative of f(x) at a point?":
        "The slope of the tangent line at that point. The derivative measures instantaneous rate of change -- how fast the function is climbing or falling right there.",
    "What does the integral of a function represent geometrically?":
        "The area under the curve. Integration sums up infinitely many infinitely thin rectangles. Newton and Leibniz independently discovered this in the 1660s-1670s.",
    "A probability must always be between ___ and ___?":
        "Between 0 and 1 (inclusive). Zero means impossible, 1 means certain. Any probability outside this range is meaningless.",
    "If two events are mutually exclusive, can they both occur at the same time?":
        "No. Mutually exclusive events cannot happen simultaneously -- like rolling a 3 and a 5 on one die. P(A and B) = 0.",
    "What is the probability of rolling a 3 on a fair six-sided die?":
        "1/6. Each face is equally likely, and there are 6 faces. One favorable outcome out of 6 total possibilities.",
    "What does it mean for a sequence to converge?":
        "It approaches a finite limit. The terms get arbitrarily close to a specific number as you go further out. For example, 1, 1/2, 1/3, 1/4... converges to 0.",
    "What is a rational number?":
        "A number expressible as a ratio of two integers (like 3/4 or -7/2). Rational numbers include all fractions, integers, and terminating or repeating decimals.",
    "Is sqrt(2) rational or irrational?":
        "Irrational. It cannot be expressed as a fraction of integers. The ancient Greeks proved this around 500 BC, and it shook their belief that all numbers were rational.",
    "In a normal distribution, roughly what percentage of data falls within one standard deviation of the mean?":
        "About 68%. This is the empirical rule (68-95-99.7). Two standard deviations capture about 95%, and three capture about 99.7%.",
    "What is a mathematical proof by contradiction?":
        "You assume the opposite of what you want to prove, then show this leads to a logical impossibility. The contradiction proves your original statement must be true.",
    "What is mathematical induction used to prove?":
        "Statements that hold for all positive integers. Prove the base case (n=1), then show if it works for n=k, it works for n=k+1. Like an infinite chain of dominoes falling.",
}


def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    path = os.path.join(script_dir, "questions", "math.json")

    with open(path, "r", encoding="utf-8") as f:
        questions = json.load(f)

    added = 0
    missing = []
    for q in questions:
        if "context" not in q:
            key = q["question"]
            if key in CONTEXTS:
                q["context"] = CONTEXTS[key]
                added += 1
            else:
                missing.append(key)

    with open(path, "w", encoding="utf-8") as f:
        json.dump(questions, f, indent=2, ensure_ascii=False)

    print(f"Total questions: {len(questions)}")
    print(f"Context added: {added}")
    already = sum(1 for q in questions if "context" in q) - added
    print(f"Already had context: {already}")
    if missing:
        print(f"\nWARNING: {len(missing)} questions had no context mapping:")
        for m in missing:
            print(f"  - {m!r}")
    else:
        print("All questions now have context!")


if __name__ == "__main__":
    main()
