
On the most recent episode of Oxide and Friends, about predictions for 2026, I was inspired by one prediction in particular.

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

Traditional "human-centric" programming languages like Python, JavaScript, Go, Rust, etc., were designed before the concept of `tokens`, and were designed to give squishy humans words they could understand to express concepts to computers.

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

## B-IR: my first LLM-centric programming language

With that background out of the way, let's get back to the prediction: that there will be a programming language designed from the start to be optimized for LLM usage. Humans don't have to read or write or undestand it. The goal is to let an LLM express its intent as token-efficiently as possible.

So naturally, I asked Gemini to design a programming language for itself to use, optimized for token efficiency!

It created **[B-IR]**, short for "Byte-encoded Intent Representation" (`beir` was right there, but okay). It also always stylized the language's name as `[B-IR]` with the brackets. Okay LLM, whatever you say.

It decided to optimize its language heavily for token usage, and to really take advantage of not needing to be readable. It wrote a [`manual.md`](https://github.com/imjasonh/b-ir/blob/main/manual.md), including this example:

> Input: "Extract 50 bytes from the 'Logs' file and send to the 'Analysis' module only if the file is not empty."
> Resulting [B-IR] Code:  ⌬[LOGS]ᚖ⫺{0}ᚕ{50}✂⫸⌬[ANALYSIS]⏀

Wow. Uhhhh, yeah. Mission accomplished I guess, that sure is unreadable!

## Bootstrapping a B-IR Compiler

This example is just an example though. There's no way to translate that mess of unicode characters into an actual runnable set of computer instructions.

So next we* got to work writing a compiler. I asked it how it would like to do that, and it chose Python, and got to work.

> \* when I say "we" I think you know I didn't have a lot of direct involvement.

This exercise hit a wall pretty quickly though, because, surprisingly, the language in question was too cumbersome to express in Python!

The mapping of B-IR operations to their associated assembly was confusing Gemini pretty badly, and it had a lot of difficulty producing a valid Mach-O binary from its Python code.

At this point I switched to Claude Sonnet 4, and asked it what it would do differently.

## TBIR: my _second_ LLM-centric programming language.
