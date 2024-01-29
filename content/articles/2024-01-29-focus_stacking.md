---
author: vigilante sculpting
date: 2024-01-29T12:52:55 -0800
tags:
- photography
- miniatures
- howto
thumbnail: https://i.imgur.com/Opz2aQu.jpeg
title: Focus stacking for fun and profit

---
Have you ever taken a photo of one of your larger miniatures, and struggled to keep the whole thing in focus?

![](https://i.imgur.com/0oxo5RW.jpeg)

> I recently had this problem, where the front of my 23cm war rig was in focus, but the back not. And if I got the back in focus, the front was not *aaaaaarrrrghhh!*

This is caused by the short focal depth of close-up miniature photography, and it makes your miniatures look *even more* miniature. Great for when you want that look. And in fact some photographers will use special tilt shift lenses or post-processing *in order* to give regular objects that miniature-like look. 

![](https://i.imgur.com/R69RApS.jpeg)
*The Merced river valley. Taken from the Mist Trail towards Yosemity Valley, CA in 2023. Post-processed in GIMP for that Miniature Look*

> Ironically, tilt-shift lenses also allow you to tilt the focal plane, in some cases giving you deeper depth of field so you don't need focus stacking in the first place. Light is weird.

But if you want to make that tank look as real as possible, or even just to show off that entire in-focus flyer in one shot...

Focus stacking to the rescue
=

This is where focus stacking comes in. If you have the patience, this can give your photos a larger depth of field, making those minis look just a tiny *(cough)* bit more realistic.

There are a couple of articles about focus stacking floating around. In this article, I want to show you my way of doing it. I am cheap, so I have some limitations about how I do this:

* I don't have a high-end DSLR. My phone camera has to do.
* The only phone I have is an android phone.
* Paying for Photoshop is out of the question.

If these limitations apply to you, then this article might be for you.

> *Heads-up*: this will mean running commands from the command-line on your PC or Mac. No one said this was easy, but it is as easy as I can make it!

Lots of photos, really?
=

Typical focus stacking requires lots of photos. That is because focus stacking subjects are typically insanely small insect compound eyes, water droplets, bed bugs or whatever, and the closer zoomed-in we go the less focal depth we get. These subjects need focus-stacking, where as our miniatures just kinda like it.

So for miniatures, we typically only need a couple of photos. It will depend on your miniature, camera and setup, but 3 or 4 photos will probably cover all the focal depth you will need.

In fact, taking too many pictures can degrade the quality of the resulting image, making the end result look as if it put on *way* too much unsharpen mask in the morning.

Garbage in, garbage out
=

To get the best results, it is better that you take photos that are as similar as possible, varying only focal length. That means keeping my phone as still as possible between individual photos. The less work we need to do later in the pipeline, the better...

This can be helped by using a tripod, but it will still be hard to keep the phone motionless while trying to change the focal length between shots.

The proper phone app can help out tremendously here.

There's an app for that
=

Enter [Open Camera](https://opencamera.org.uk/). This is an amazing app that can teach your Android phone camera some new tricks.

It has a focus stacking mode, which allows you to set the near focal length and the far focal length, and the number of pictures to take. It will then take that many photos as quickly as possible, incrementing between the near and far focal lengths.

All you have to do is hold the camera as steady as possible, or use a tripod if you have one.

> I also have focus-peaking enabled under the Open Camera Preview settings, as well as zoom-to-focus set at 2x. This makes setting up the near & far focal lengths super easy.

Free Hug(in)s!
=

Ok, so you captured a couple of shots, now how do you go about getting the final image?

Not so fast! First you have to align your set of images as close as possible. Sure, you took care when you shot the photos, but the very act of varying focal length will slightly alter the image. And we need pixel-perfect alignment to be able to figure out which pixels are in focus.

To do this, you will need [Hugin](https://hugin.sourceforge.io). It is a very capable desktop application that is typically used for HDR photography.

> Quite similar to focus stacking, HDR post processing also needs to align images. And that is what Hugin can do for us.

Best of all, Hugin is free software!

I have a Mac, so I installed Hugin via [Homebrew](https://brew.sh/). But if you just want to download and install a package, then head over to [the Hugin Download page](https://hugin.sourceforge.io/download/) and grab the relevant pre-compiled binary for your system. Easy peasy.

Line 'em up!
=

After this, we need to run the `align_image_stack` from the Hugin installation director on our set of images. This will slightly disort the images that you took previosusly, so that the pixels line up perfectly.

For my mac, I open a terminal and change to the directory where I downloaded the images from my phone. Then I run

```
$ /Applications/Hugin/tools_mac/align_image_stack \
    -m -e \
    --use-given-order \
    -a _huginoutput 
    *.jpg
```

where

* The `-m` option will "Optimize field of view for all images, except for first. Useful for aligning focus stacks with slightly different magnification". Since I know my camera lens changes distortion at different focal lengths, I use this option.
* `-e` assumes the images are "full frame fish eye". I use this because it gives me results. You should too.
* `--use-given-order` lets the software know that I want to align the images from the first to the last.
* `-a` specifies the prefix to use for the processed images.

This will churn for a bit. Once the program finishes (with no error messages!) we are ready for the next step.

*However*, if the program complains about not finding any control points, eg.

```
After control points pruning reference images has no control
points Optimizing field of view in this case results in undefined
behaviour. Increase error distance (-t parameter), tweak cp
detection parameters or don't optimize HFOV.
```

there are a number of extra command options we can pass to `align_image_stack`, to get proper control points & alignment. The most useful ones will be 

* `-i` which will try to align the centers of the images. Try this especially if you don't have a tripod.
* `--corr=0.8` which lowers the correlation coefficient threshold to 0.8 (from 0.9). Try this if there is some noise in your images. This lowers the bar for what the program will consider as "matching" points between images.
* `-c 500` This increases the number of control points to try from 8 to 500. The more we use, the better the outcome *could be*. Not always, but worth a shot.
* `-g 3` The images are usually broken into 5 rows and 5 columns, and control points are found between images within these blocks. If the control points just don't wanna be found, try inreasing the block size, ie. 3 rows and 3 columns in this case.

If `align_image_stack` fails with

```
No Feature Points
Bad params
An error occurred during optimization.
Try adding "-p debug.pto" and checking output.
Exiting...
```

then it probably means that the images are way too dissimilar and they can't be aligned. Go back a step and re-take better pictures...

Stitch 'em up!
=

We should now have a bunch of lined-up `_huginoutput*.tif` images. We now need to find the parts from each image that are in focus, and stitch them together like Frankenstein.

To do this, we will use another program from Hugin, called `enfuse`. It is usually used to identify the correctly *exposed* parts of each image for HDR photography, but the process is so similar that we can abuse it to find the correclty *focused* parts instead.

To do this, run this command from the same directory:

```
$ /Applications/Hugin/tools_mac/enfuse \
    --exposure-weight=0 \
    --saturation-weight=0 \
    --contrast-weight=1.0 \
    --hard-mask \
    --gray-projector=luminance \
    --contrast-window-size=15 \
    --output=output.tif  \
    _huginoutput*.tif
```
	
This is quite a mouthful, so I'll break it down:

* Setting `contrast-weight` to 1.0 and `exposure-weight` & `saturation-weight` to 0 is what gets us focus stacking. We are telling `enfuse` to identify the parts of each image that has high variations in contrast (ie. detail). We don't care about saturation or exposure, because we are not dealing with HDR.
* We want a `hard-mask`. This means `enfuse` should use the parts of each image that are the most in focus, and *only* use that part of that image. We don't want a weighted average over the entire image group, because that will soften the focus - which is not what we want.
* I choose to use `luminance` to determine the contrast, but there are other options such as `anti-value`, `average` and `l-star`. This is a field to play with, and some alternative choices may give you better results in some circumstances
* I set `contrast-window-size` to 15, up from the default of 5. This determines the size of the region around each pixel that is used to determine its contrast. For the size images I am getting from my camera (4608 × 2592) this slightly bigger size gives me good results, but YMMV.

`enfuse` will output the resulting focus-stacked image as `output.tif`. This should, if everything went correctly, produce a pretty cool all-in-focus photo of your miniature subject. Congrats!

The results
=

Here are some input images I took with my phone, after they were aligned with `align_image_stack`:

![](https://i.imgur.com/4JzPcR2.jpeg)
![](https://i.imgur.com/lDvoegZ.jpeg)
![](https://i.imgur.com/W5x3zM5.jpeg)

As you can see, the first image has the cab in focus, the second has the middle section in focus, and the third has the tail-end and the flags in focus.
Here is the final focus-stacked result, directly from `enfuse`:

![](https://i.imgur.com/Opz2aQu.jpeg)






