# Chainguard&#x27;s image tagging philosophy: enabling high velocity updates (pt. 1 of 3)

*Jason Hall*

*November 13, 2023*

***Part 1 of 3 in the series.****Part 2**](https://www.chainguard.dev/unchained/chainguards-image-tagging-philosophy-enabling-high-velocity-updates-pt-2-of-3)**covers content-addressed tagging, comparison with Git Tags, and mutability considerations.****Part 3**](https://www.chainguard.dev/unchained/chainguards-image-tagging-philosophy-enabling-high-velocity-updates-pt-3-of-3)**covers how Chainguard deploys by digest, why sometimes digests aren’t enough, and what you can do about it.**

![An image of old suitcases stacked on top of each other.](../blog-images/tagging_philosophy_part1_img1.jpeg)

## Introduction to Chainguard’s image tagging philosophy

Chainguard produces lots and*lots*of images, and aims to provide inhumanly fast updates to them. But we also need to*identify*those images in a meaningful way, which can lead to confusion. We wrote this series to explain how we tag images today to achieve maximum update velocity without sacrificing clarity or usability.



You may be thinking: What? Why not just tag images with the immutable version of the thing?`cgr.dev/chainguard/go:1.21.1`right? There's only one Go 1.21.1. Easy, done. Why is there so much of this doc left?



*Not so fast!*



Wolfi and Chainguard Images can fix vulnerabilities in tools without waiting for the upstream to release patches. We created and maintain a whole distro purely for this purpose.



It's unlikely, but if there's a CVE in Go 1.21.1 and the Go team is uncharacteristically slow in releasing a fix in`1.21.1`, we could patch it into`1.21.1`, and release it as`1.21.1-r2`. The original package is also available as`-r1`, future fixes would be available in`-r3`,`-r4`, etc. We call this the "epoch" number. The`r`is for "epoch".



We do this to packages all the time: to patch vulnerabilities, to remove unnecessary bloat, to rebuild the same source with newer tools, and to address bugs in our build configs and build tooling. The upstream version doesn't change – it's still what the Go team calls`1.21.1`– but we may produce many different versions of that version of Go.



Okay, so just immutably tag it as`cgr.dev/chainguard/go:1.21.1-r2`and never change it. What's so hard about that?



That works perfectly… if there's only one package in the image. In reality this is almost never the case. The image is tagged as`go:1.21.1-r2`but there are other tools available in that image: at the time of writing this, that Go image has about 50 distinct packages in it, things like`bash`,`busybox`,`git`,`glibc`,`openssh`,`make`,`zlib`, and more. These packages are software, and as we all know, software has vulnerabilities. Vulnerabilities that we want to fix!



When we fix a vulnerability in`bash`, we want to make sure that fix gets rolled out to every image that includes`bash`, like our`go:1.21.1`image. But the version of Go is still the same,`go:1.21.1-r2`. So that's what we'll keep tagging it with. The image tagged`1.21.1-r2`will get that`bash`j fix, and fixes for any of the other packages in the image.



When you opt in to pulling`go:1.21.1-r2`you're opting in to a consistent version of Go, and potentially floating versions of all the other packages – this means you get CVE fixes in`bash`, etc., and also patch, and minor, and even major version releases of`bash`, and every other package.



This is the case for every image, and can get even more complicated for certain images. For example, the`pulumi`image includes`pulumi`, as you might expect, but also`nodejs`,`go`,`python`,`pip`,`openjdk`,`maven`,`dotnet`,`sqlite`, and all of those tools' dependencies.



There are more than 100 packages in total, many of which are large, complicated projects, the kind you wouldn't be surprised to find having a new vulnerability reported every couple months. Each. But we'll only tag the image with Pulumi's version.



In this scenario, you probably want to be pulling (or at least following) the`:1.21.1`version stream, since that will get a constant supply of vulnerability fixes and improvements, while keeping the version of Go consistent.



## Tag updates: Everyone's doing it!

If you happen to be using the Docker official image for Go,`golang:1.21.1`, you're likely already getting exactly this behavior. That image also contains many other tools,`bash`,`git`and the rest, and as updates are released to those tools, they'll get included in new versions of the`golang`image, which they also tag with`:1.21.1`for the same reason we do.



The official`golang:1.21`image gets rebuilt periodically by Docker, from [this Dockerfile](https://github.com/docker-library/golang/blob/d1ff31b86b23fe721dc65806cd2bd79a4c71b039/1.21/bookworm/Dockerfile), and tagged with the latest Go version (`1.21.1`as of right now), and you can see it does`apt-get update && apt-get install`to install other tools like`gcc`and`make`.



The image is based on`buildpack-deps:bookworm-scm`([Dockerfile here](https://github.com/docker-library/buildpack-deps/blob/3e18c3af1f5dce6a48abf036857f9097b6bd79cc/debian/bookworm/Dockerfile)) which also`apt-get install`s a few dozen other dependencies. When Debian releases updates for any of those dependencies, Docker builds and tags the image with the Go version (`:1.21.1`), which will henceforth include those new updates.



You can observe changes to the official Go image over time. I've set up a [GitHub repo](https://github.com/imjasonh/image-scraper/)that periodically collects the current digest of certain tagged images, and you can see [changes](https://github.com/imjasonh/image-scraper/commits/main/index.docker.io/library/golang%3A1.21.1)to the`golang:1.21.1`tag there.



This behavior is nothing new; the difference with Chainguard is the cadence at which packages are updated and released – Wolfi aims to release new versions as soon as possible, while Debian is much more*…conservative*.



## Comparing Bitnami Rolling Tags

[Bitnami's tagging scheme](https://docs.bitnami.com/tutorials/understand-rolling-tags-containers/)is similar to ours (`3.4.13-debian-10-r8`) except their last component (`r8`) will not change, unless the main package is rebuilt with a new epoch number. Bitnami's package versioning scheme covers updates to the dependencies of the package, so an update to a dependency is reflected in the new version epoch. Bitnami automates these updates, including any necessary dependency updates outside the "main" versioned package.



As a result, their guidance is:



*It is strongly recommended to use immutable tags in a production environment. This ensures your deployment does not change automatically if the same tag is updated with a different image.*



This makes sense in their model;`r8`will be the same image forever, you can expect that tag to be immutable.



In our case, Wolfi's packages are finer-grained and express other dependencies that get brought into an image at build time. This is merely a trade-off between many finer-grained packages and monolithic packages that contain their dependencies.



**A previous version of this blog post incorrectly captured how Bitnami handles tagging in regard to update automation. This post has been updated to reflect the correct information about tagging protocol and update cadence used by the Bitnami team. Thank you to their team for reaching out to provide accurate details for our community.*



## What’s next

In the next installment of Chainguard’s Image Tagging Philosophy, we’ll discuss other tagging schemes, comparison with Git Tags, and mutability considerations. The final installment covers topics related to image digests.
Share