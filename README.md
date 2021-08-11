# vigilantesculpting.github.io

This is my hobby website code, dedicated to scratchbuilding, painting, sketching and drawing.
It should be available at [https://www.vigilantesculpting.com](https://www.vigilantesculpting.com)

## About the code

The entire site is built from scratch using a template-framework built in Python.
Initially taking inspiration from Sunaina Pai's [makesite.py](https://github.com/sunainapai/makesite),
after some thought I decided to rewrite the entire thing, added a custom control flow
language to structure the templates, and a custom logic language to do calculations.

Oh, and a custom tokenizer and a structured namespace dictionary, which acts as a context
for storing data.

All of this code in on github in separate repos, so you can pick and choose what you want:

- [nsdict](https://github.com/vigilantesculpting/nsdict) is the namespaced dictionary, basically a tree structure for storing data,
- [tokenyze](https://github.com/vigilantesculpting/tokenyze) does tokenizing of input strings for pretzyl,
- [pretzyl](https://github.com/vigilantesculpting/pretzyl) is a stack-based forth-like functional language, for doing calculations and transforming data,
- [solon](https://github.com/vigilantesculpting/solon) is the control flow template language, for composing pieces of text and data, and finally
- [rezyn](https://github.com/vigilantesculpting/rezyn) is the framework that binds it all together, and takes my blog posts to actual webpages.

I decided to keep copies of the individual project sources in each repo that needs them.
So for example, rezyn contains copies of nsdict.py, tokenyzer.py, pretzyl.py and solon.py

This repository adds a modification to rezyn, by extending the rezyn.Rezyn class to do some custom
blogpost-processing, before rendering the text output. It contains all of the above mentioned source code.

As such, there are no subrepos or other shenanigans, since the project(s) are simple enough to manage as-is.

At least, for now.

## Why? And why not just use Jekyll? Are you crazy? Or stupid? Or both?

If you know me, you know I like doing things from scratch (check out my blog, it is full
of scratchbuilt stuff). This means I get to customize everything, and learn some things along the way.

Of course, most template engines start looking the same, after a while, but this one is fairly special I think.

It runs pretty fast, for a python program, crunching the 300-odd blogposts in about 3 seconds.
Given that the code does not cheat and use `eval`, I think that is ok. 

The pretzyl and solon languages are pretty cool, self-consistent and minimal, and most of all
they allow me to figure out why a template fails to compile pretty quickly, through a fairly 
judicious use of exeptions and error tracing.

The system allows me to write the templates in a way that makes sense to me, and the result
is pretty to look at.

Cheers!

