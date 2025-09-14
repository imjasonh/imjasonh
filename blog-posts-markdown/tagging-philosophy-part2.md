# Chainguard&#x27;s image tagging philosophy: enabling high velocity updates (pt. 2 of 3)

*Jason Hall*

*November 15, 2023*

***Part 2 of 3 in the series. In****Part 1**](https://www.chainguard.dev/unchained/chainguards-image-tagging-philosophy-enabling-high-velocity-updates-pt-1-of-3)**, we explored tagging philosophy and tag updates from a high level.****Part 3**](https://www.chainguard.dev/unchained/chainguards-image-tagging-philosophy-enabling-high-velocity-updates-pt-3-of-3)**covers how Chainguard deploys by digest, why sometimes digests aren’t enough, and what you can do about it.**

****

## **Content-addressed tagging**



In the previous post, we talked about how Chainguard constructs its tags when the image contains versioned multiple components.



Sometimes at this point, people have the dubious idea that we could tag the image with the versions of a few of the most important packages in the image. Even more dubiously, we could tag an image with all the versions of everything in the image.`go:1.21.1-git4.5.6-bash7.8.9-...zlib9.8.7`and so forth. That way you could pin exactly to specific versions, and you'd always know exactly what versions were in the image at a glance, and update images deliberately as needed.



Let's ignore the practical UX issues of such a long tag, and the combinatorial explosion of tags you'd need to wade through to find the image you want – we can invent search/browsing UIs for finding the tag, and if the tag gets too long (they're capped at 128 characters) we can invent a hairbrained scheme to encode and compress that information so it fits in the tag. If you still think this is a good idea, you're not totally wrong: you've basically invented*image digests*, which already exist.



The image digest is a 64-character hex-encoded SHA-256 hash of the contents of the image. It's not just based on the packages contained in the image, but the contents of every*file*in the image, and it covers metadata about the image too – the environment variables, entrypoint, user, creation timestamp, everything. Changing any of these bits of information would result in a new image digest.



When pulling an image by digest, container runtimes check that the contents they pulled match the given digest, so you don't even have to take our word for it, the digest is the canonical ID of an image by its contents. And it's shorter than that 128-character tag scheme we almost invented earlier!



## Comparison with Git Tags



If you're familiar with Git, you may be thinking at this point that a digest is sort of like a [commit SHA](https://git-scm.com/docs/git-commit)– that's not an accident! If you're not familiar with Git, a Git commit SHA is a 40-character hex-encoded SHA-1 hash of the contents of a given state of the source code. Changing a file's contents or metadata would result in a new commit SHA.



Like container images, Git has a concept of [tags](https://git-scm.com/book/en/v2/Git-Basics-Tagging). When you want to share the state of a source code with others, you can apply a tag like`1.0.0`, and someone else can`git checkout 1.0.0`to browse and build that version of the source code. Git's internals map the tag`1.0.0`to some commit SHA, and act as a memorable name for that commit.



Container image tags are similar. Instead of having to deal with a long inscrutable hex-encoded digest of all of an image's contents, you can deal with a tag like`:1.0.0`and know that that's version 1.0.0 of the software (probably).



Except, just like with Git tags, image tags are mutable. In both cases, anyone with permission to push to the repo can also update and push a tag. The tag`1.0.0`can be one thing today, and another thing tomorrow. This could be malicious, but usually it's a well-meaning mistake. In any case it's bad news if you want to know exactly what's what. And we do.



In practice there's a convention that Git tags shouldn't change, and some ancillary systems (like [Go's module system](https://go.dev/ref/mod)) detect and fail if tags move since the last time they were seen, but those tend to only work if they've seen the previous tag's commit before. Some systems in the container image ecosystem also detect and warn on changing tags, but they're also incomplete solutions.



Aside from tags, Git also has the concept of [branches](https://git-scm.com/docs/git-branch). Git branches also point to commits, but Git's expectation is that they move along with new commits – when you`git commit`something that's on the`main`branch, the`main`branch moves to point to the new commit. But in either case, this is just a convention. With enough mucking in Git's internals, you can point the`main`branch to point to a different branch entirely, or a new orphaned commit, or basically anything if you're creative enough. Git's crazy like that.



Container images don't have the concept of branches. Instead, the ecosystem seems to have broadly adopted a convention that some image tags should be*expected*to move (like Git branches), and some should be*expected*not to move (like Git tags).



Image tags named like`:latest, :1`,`:staging`, and`:rc`are generally expected to change. Image tags like`:1.21.1-r2`are at least theoretically expected to stay put. And in some cases, it's not clear without more information whether a tag named`:1.20`should be expected to move or not.



And in any case, as demonstrated above, there's a lot more to that single version tag than meets the eye, especially if you want to deliver image updates that fix vulnerabilities in all of the image's components. Which we very much do!



## Image Tags are Mutable, Even Immutable Tags



Some smart folks, trying to save themselves from the widespread convention that some tags should be expected to move and others shouldn't, decided to make their registry enforce immutable tags. This was a well-meaning, but incomplete, solution.



First of all, at least the way [ECR](https://aws.amazon.com/ecr/)implements them, tag mutability is configured at the repository level. This means that every tag applied to the`go`image is either mutable or immutable. But as we saw before, the widespread convention is that some tags are expected to be mutable (`:latest`) and some aren't (`:1.21.1-r2`), and some are "it's complicated" (`:1.20`). You can solve this in ECR by having two repositories – one for mutable tags and one for immutable tags – but that can get very cumbersome, especially if you also want to limit access to those repositories differently.



Secondly, since enabling immutable tags is just a configuration of the repository, it can be disabled as easily as it can be enabled. As with changing Git tags, this could be malicious, but usually it's a well-meaning mistake. Because some tags are expected to be mutable, an image push workflow might disable tag immutability for the repository, push an update to`:latest`, then re-enable immutability. The best of both worlds right? Sure, except for race conditions, or failures that cause the workflow to exit before re-enabling immutability.



A well-meaning SRE might disable tag mutability during a late-night outage to get production back up and running, and simply forget to re-enable it. The only thing worse than mutability is ambiguity about mutability.



Immutable tags are like having a plastic flip-up cover on a Big Red Button. Sure, it's good to have a safeguard against accidental changes, but when it's really important, you want something more than a piece of plastic involved.

![Image of red emergency button with plastic cover flipped up, ready to be pressed with sarcastic subtitle: resist the urge to push the button! Reflecting why immutable tags aren't enough in tagging.](../blog-images/tagging_philosophy_part2_img1.jpeg)

Resist the urge to press the red button!

If immutability is really what you're after, accept no substitutes – you want*digests*. I know, I know, they're long inscrutable hex-encoded gibberish, but they have one job and they do it well: they succinctly and provably describe*all*of the contents of an image, and they'll never change.



## What’s Next



In the third and final installment of Chainguard’s Image Tagging Philosophy, we’ll dive into how Chainguard deploys by digest, why sometimes digests aren’t enough, and what you can do about it.
Share