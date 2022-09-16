---
author: vigilante sculpting
date: 2022-09-16T15:55:28 -0700
tags:
- semiotic
- keyboard
- keypad
- macrokeyboard
- alien
- weylanyutani
thumbnail: https://i.imgur.com/6y2ksgE.jpeg
title: Semiotic keyboard, wip
---
I have really started enjoying using my [url=https://www.xp-pen.com/product/461.html]XP-Pen drawing tablet[/url] with [url=https://krita.org/]Krita[/url] now,
but the one thing that bothers me is that I still need the keyboard, even for simple tasks such as canvas navigation, brush size/opacity, etc.
(Sure, you can drive all of this with the pen/tablet, but using keyboard shortcuts is an easy way to stay productive).

To use my keyboard, I have to sit in an awkward position, since the keyboard and tablet don't fit side by side. Especially when I want to tilt the tablet, since then I have to reach
behind the stand in order to access the keyboard. This inconvenience has made me look into getting a 12-key/3-knob macro keyboard. But if you know me, you'll know that I love a good yak shave. Plus I don't like spending money.

Thus, I started tearing apart an old Microsoft 1558 external keypad that I had lying around. This is a very simple keyboard, and it was easy to solder on a couple of leads.

[img]https://i.imgur.com/Toyir79.jpeg[/img] IMG_20220913_142705542.jpg

Then I hooked it up to my Adafruit Feather using a breadboard, and hacked up a bit of code as proof of concept, to see if I could homebrew my own macro keyboard. And guess what, it works.

[img]https://i.imgur.com/DdzNPvK.jpeg[/img] IMG_20220915_202124622.jpg

The plan is to add 3 rotary encoders on the side, so that I then have a one-handed 17 buttons / 3 knobs macro keyboard with which I can generate whatever
key combinations I want. This should give me enough control over Krita so that the only time I have to dig around for my large keyboard (well, it is a [url=https://www.keychron.com/products/keychron-k6-wireless-mechanical-keyboard]Keychron K6[/url], so it isn't
[i]that[/i] large) is when I need to type in file names and whatever.

Then, it has to be given a good housing and some kinf of lettering, because style.

For the housing, I have this old printer-control panel housing, that I will cut to size and greeblie up. The rotary encoders will get some junk knobs, with a better grip.

[img]https://i.imgur.com/DNWyv2i.jpeg[/img] IMG_20220915_202749621.jpg

For the button labeling, I decided that since it will be a shortcut keypad, there is no use putting dedicated letters or words on the keys, since I should be able to change layout 
at will, if I manage to get [url=https://qmk.fm/]QMK[/url] running on the board.

And what better set of keyboard symbols than the [i]Semiotic Standard For All Commercial Trans-Stellar Utility Lifter And Heavy Element Transport Spacecraft[/i], courtesy of [url=http://www.roncobb.net]Ron Cobb[/url].

[img]https://i.imgur.com/gu1rH1J.jpeg[/img] ron-cobb-semiotic1.jpg
[img]https://i.imgur.com/ZTEk4EO.jpeg[/img] ron-cobb-semiotic2.jpg

Here is the layout I've come up with:

[img]https://i.imgur.com/6y2ksgE.jpeg[/img] labels.jpg

I plan to properly weather the white housing up, so it looks more like a 90's beige computer case. The keyboard buttons will be sprayed white and weathered in the same way.
