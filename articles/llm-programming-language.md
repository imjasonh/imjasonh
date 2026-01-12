# An LLM-optimized Programming Language

http://articles.imjasonh.com/llm-programming-language.md<br>
Jason Hall<br>
_First published January 11, 2026_

> [!NOTE]  
> This article describes heavy use of LLMs, but the article itself was written completely by me, a human, without LLM augmentation.

On the [most recent episode of Oxide and Friends, about predictions for 2026](https://oxide-and-friends.transistor.fm/episodes/predictions-2026), I was inspired by one prediction in particular.

You can listen to it yourself, starting at around 35 minutes in. The [transcript](https://oxide-and-friends.transistor.fm/episodes/predictions-2026/transcript) says:

> I have one more [...] but I feel like it might be a too ambitious.
> 
> I think this is the year we see LLMs have a programming language, which is not human intelligible.
> 
> That there is a programming language by and for LLMs.

I don't know about you, but that sounded like a challenge to me!

This isn't the first time I've encountered this idea, for what it's worth, but it was the first time I encountered it bored at home on a Sunday with my laptop calling to me.

But first...

## Background

The idea is, basically, that LLMs consume and produce **`tokens`**, and that these are a precious resource. When reading source code or prompts or anything, they first chunk up the input into `tokens`, then use those as coordinates to traverse a gigantic multi-dimensional semantic space to figure out what you meant, and what they want to do.

Traditional "human-optimized" programming languages like Python, JavaScript, Go, Rust, etc., were designed before the concept of `tokens`, and were designed to give squishy humans words they could understand to express concepts to computers.

Compilers or interpreters take those words, and translate them as closely as possible to the original human intent, to [assembly code](https://en.wikipedia.org/wiki/Assembly_language), which gets processed by an assembler into machine code, which processors in computers execute.

As an example, some C code like this...

```c
int square(int num) {
    return num * num;
}
```

...gets translated by the compiler into assembly code that looks like...

```
square:
        push    rbp
        mov     rbp, rsp
        mov     DWORD PTR [rbp-4], edi
        mov     eax, DWORD PTR [rbp-4]
        imul    eax, eax
        pop     rbp
        ret
```

_This example is taken directly from the excellent [Compiler Explorer](https://godbolt.org/) -- if this topic is interesting to you, stop reading this and start playing over there._

This lower-level representation is generally not intended to be written or read directly by humans -- that's what we have compilers for -- but in some situations it's necessary for a human to interact with it. It's not very ergonomic, sort of by design. This is the middle-ground between what a human should be able to understand, and what a computer's processor needs to execute instructions.

## B-IR: my first LLM-optimized programming language

With that background out of the way, let's get back to the prediction: that there will be a programming language designed from the start to be optimized for LLM usage. Humans don't have to read or write or undestand it. The goal is to let an LLM express its intent as token-efficiently as possible.

So naturally, I asked Gemini to design a programming language for itself to use, optimized for token efficiency!

It created **`[B-IR]`**, short for "Byte-encoded Intent Representation". I pronounce it like "beer" in my head, but I don't know whether that was the intent and I never asked.

It also always stylized the language's name as `[B-IR]`, with the brackets. Okay LLM, whatever you say.

It decided to optimize its language heavily for token usage, and to really take advantage of not needing to be readable. It wrote a [`manual.md`](https://github.com/imjasonh/b-ir/blob/17a87cae87e8f17e071379f393c96c2266ad78f9/manual.md), including this example:

> Input: "Extract 50 bytes from the 'Logs' file and send to the 'Analysis' module only if the file is not empty."
> Resulting [B-IR] Code:  ⌬[LOGS]ᚖ⫺{0}ᚕ{50}✂⫸⌬[ANALYSIS]⏀

Wow. Uhhhh, yeah. Mission accomplished I guess, that sure is unreadable!

## Bootstrapping a B-IR Compiler

This example is just an example though. There's no way to translate that mess of unicode characters into an actual runnable set of computer instructions.

So next we* got to work writing a compiler. I asked it how it would like to do that, and it chose Python, and got to work.

> \* when I say "we" I think you know I didn't have a lot of direct involvement.

The only goal of this Python compiler was to be able to translate a minimal subset of [B-IR] code into assembly. Once the Python version of this was implemented, we would be able to write a [B-IR] compiler _in [B-IR] itself_, and then we would be off to the races.

This exercise hit a wall pretty quickly though, because, surprisingly, the language in question was too cumbersome to express in Python!

The mapping of B-IR operations to their associated assembly was confusing Gemini pretty badly, and it had a lot of difficulty producing a valid Mach-O binary from its Python code.

At this point I switched to Claude Opus, and asked it what it would do differently.

## TBIR: my _second_ LLM-optimized programming language.

Claude Opus threw `[B-IR]` straight out the window, and replaced its multi-byte unicode opcodes with single-byte opcodes.

It kept the theme of unreadability alive though, and chose characters in the range `0x80-0x8B`. Real classics like [`padding character`](https://www.compart.com/en/unicode/U+0080), [`next line`](https://www.compart.com/en/unicode/U+0085) and [`partial line down`](https://www.compart.com/en/unicode/U+008b). It also dubbed its take on the language TBIR, short for "text-based B-IR" -- it didn't seem to care what [B-IR] meant. I can relate.

When we got to work on the Python bootstrap compiler, and chugged away for a bit.

Surprisingly, on its own, it decided that maintaining the unreadable character opcodes was tripping it up too, and switched to short English words to express its operations. From its README:

> ```
> init                    # Open argv[1] for reading
> fetch                   # Read one byte (x21=count, w23=byte)
> emit                    # Write byte from stack to stdout
> print "text"            # Write literal string to stdout
> ```

With this optimization it was able to write a Python script to compile TBIR into Arm64 assembly in a [Mach-O file](https://en.wikipedia.org/wiki/Mach-O), and run it!

```
python3 birc.py source.tbir > output.s
clang -arch arm64 output.s -o program
```

With that bootstrap compiler in place, Claude could write simple programs like `cat.tbir`:

```
# cat.tbir - Copy input to output
# The simplest useful B-IR program

init            # open input file
:loop
  fetch         # read one byte
  emit          # write it
  loop loop     # repeat until EOF
exit
```

It even wrote [its own compiler in TBIR](https://github.com/imjasonh/b-ir/blob/f73a412b2c8ef960fe9b3ea284425cb862449898/l1-compiler.tbir), clocking in at just under 700 lines of code.

With this bootstrapped compiler, we were off to the races.

## ...except...

I don't know about you, but I don't find TBIR to be that _...impressive?_ When I heard the prediction, I assumed the LLM-optimized language would be more ...exotic? Less comprehensible to mere mortals?

This sort of just looks like assembly code, with some sugar. I'm pretty sure a human could read and write TBIR, if they had to.

I wanted _more._

## What does "LLM-optimized" even _mean?_

Sure, being able to express a concept in as few tokens as possible is _important_, but is that it? It seemed like hyper-optimizing that actually led to worse outcomes, and maybe something more like assembly code is the optimal language for token usage. Maybe assembly code is _actually_ the best language for that -- the whole process demonstrated that Gemini and Claude are both perfectly capable of reading, writing, understanding and debugging assembly issues. Remarkably good even. There must have been lots of assembly in its training data.

Maybe they even got to spend an afternoon playing around with Compiler Explorer.

That made me think that maybe an existing language is actually already LLM-optimized in some way, because for popular languages like Python and JavaScript there's _tons_ of training data out there. And not just huge code dumps, but the human language around that code -- design docs, readmes, code reviews, bug reports, release notes, tutorials, everything. Maybe the most LLM-optimized language had been ✨inside us the whole time✨.

Nah, screw that, we're giving it another shot.

I'd gotten too focused on LLM token optimization specifically, and neglected to think about what else might make an LLM-optimized language _experience_ better. Aside from token optimization, there are other things that trip up LLMs.

**Ambiguity** is a huge problem for LLMs. For example, when they process some variable `foo`, they need to be able to understand whether that's a local or global variable. If it's present in both scopes, it has to figure out which `foo` it's talking about.

Loose typing is similar: if `foo` can be an integer at one point and later a string, the LLM has to spend some of its precious tokens and weights keeping that straight. 

When an LLM inevitably gets confused by that ambiguity, the compiler or interpreter will tell it what's wrong, and the LLM can fix it, but that loop wastes _many_ more tokens than would have been optimized by a slimmer syntax.

**Indentation** also trips up LLMs, even though they've seen plenty of Python to know better. Having whitespace be syntactically meaningful means that it's very important for a specific number of tokens to be emitted, and LLMs are not very good at counting.

**Remembering Intent** is another killer. When a user prompts the LLM to add some behavior to the program, the LLM needs to remember that intent, for as long as that behavior should live. LLMs are generally pretty good at handling this in human-optimized languages, by adding comments -- sometimes _excessive_ comments -- saying what it's doing, so it can remember later.

These comments aren't even necessarily so a human knows what's going on, these can really just be useful for the LLM to remember things related to the surrounding code. An LLM-optimized programming language would still have comments!

I also made up a term, **Validation Locality**. While an LLM is writing code, it should also be writing tests that validate that code. In languages like Go or Python, that tends to mean writing `foo.go` and `foo_test.go` as separate files. This means that those two contexts are relatively far apart in the LLM's context window. Rust lets you write tests directly alongside the code being tested, which is an improvement, but those test methods are still outside the function under test. This separation is for the benefit of the human user, to disambiguate the code that runs in the program from the code that tests the code.

An LLM-optimized programming language could have test code intermixed with the program code, and could better understand they're doing different things.

There's honestly a lot to think about when you step back and consider why our programming languages are the way they are.

With these insights in mind, I started a new conversation with Gemini, and it clued me in to even more.

## Loom - my third LLM-optimized programming language

Gemini came up with **Loom**, ("Language for Object-Oriented Models"), which is not only token-dense, but also has tight unambiguous scoping, and whose functions must express their inputs and outputs, including preconditions and post-conditions (e.g., "returns a number less than 100", or "takes a string matching this regex").

In Loom, stack traces are augmented with unique error codes that map to specific prompts to fix those errors. In Rust, you might see an error message like

```
5 |     let scores = inputs().iter().map(|(a, b)| {
  |                  ^^^^^^^^ creates a temporary which is freed while still in use
6 |         a + b
7 |     });
  |       - temporary value is freed at the end of this statement
8 |     println!("{}", scores.sum::<i32>());
  |                    ------ borrow later used here
  help: consider using a `let` binding to create a longer lived value
  |
5 ~     let binding = inputs();
6 ~     let scores = binding.iter().map(|(a, b)| {
  |

For more information about this error, try `rustc --explain E0716`.
```

_(copied from the great [Julia Evans](https://jvns.ca/blog/2022/12/02/a-couple-of-rust-error-messages/))_

This is a _great_ error message for humans. It's as clear as it can be, direct, and even recommends how to fix it. But, that's a lot of tokens for an LLM to process each time it forgets a `let`.

In Loom, it might only return `E0716` and the LLM should be responsible for knowing how to fix that.

Loom's spec is [**here**](https://github.com/imjasonh/b-ir/blob/376bda1c2c63f9c1954ecf63af0a5a59815ff7b5/loom.md)

Here's a Loom code snippet that Gemini produced:

```
# Define Schema: {In:None, Out:f64}
$tax_calc:
  billing.get_inv 
  -> last(3) 
  -> ? (count==3)  // Correctness guard: Halt if < 3 invoices exist
  -> map(.tax) 
  -> sum 
  -> !result       // Atomic commit
```

I don't know about you, but this still doesn't exactly scream to me "not human intelligible"! I've definitely seen code in many languages that's less intelligible than that.

I'm optimistic that Loom may have some good ideas in it. And to be clear, they aren't _my_ ideas. I'm going to have Claude hack on the bootstrap compiler and write more when that's done.

-----

If any of these topics are interesting to you too, I _strongly_ suggest chatting with your favorite LLM about it. It's been very enlightening thinking about what programming languages are _"for"_, and what one might look like in a post-LLM future.

It's never been easier or faster to take an idle idea and take it to a full-blown running program. And with any luck, we'll have a programming language made for LLMs, that makes it even faster. 😄

