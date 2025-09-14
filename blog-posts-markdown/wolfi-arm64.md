# Building Wolfi from the ground up and announcing arm64 support!

*Jason Hall*

*January 10, 2023*

"To make a distro, you must first make a smaller distro." - Ariadne Conill



Wolfi is a lightweight "un-distro" built from the ground up with a focus on transparent and trustworthy supply chain security. To learn more, see our [previous announcement](https://www.chainguard.dev/unchained/building-the-first-memory-safe-distro?utm_source=blog&utm_medium=website&utm_campaign=FY25-EC-Blog_sourced).



## Background

What's an "un-distro" anyway? And what does "from the ground up" even mean exactly? When we say "un-distro" we mean that Wolfi provides a set of packages like you'd get from a regular distro; for example, tools like curl, go, rust, python, and libraries like libxml, libssl, libcap. With other distros you might install these with a package manager like [apt](https://en.wikipedia.org/wiki/APT_(software))or [rpm](https://en.wikipedia.org/wiki/RPM_Package_Manager). Wolfi reuses the [apk](https://docs.alpinelinux.org/user-handbook/0.1a/Working/apk.html)package format and package manager used by Alpine. Unlike other distros, Wolfi doesn't include a [kernel](https://wiki.debian.org/Kernel). Instead, it only provides packages, and relies on a kernel being provided by an underlying container runtime. This means that Wolfi is optimized for containerized environments like Kubernetes, and you can't (currently!) install Wolfi directly on hardware. Wolfi packages are built from upstream source, using our custom build tool for apk packages,[Melange](https://github.com/chainguard-dev/melange).



For example,[Wolfi's curl package](https://github.com/wolfi-dev/os/blob/main/curl.yaml)fetches source from https://curl.se and builds it with [make](https://www.gnu.org/software/make/). But where's make come from? Well make is also built from source,[using make](https://github.com/wolfi-dev/os/blob/main/make.yaml). Wait*what*?!! Where does*that*make come from?!



Buckle your seatbelts, this is where it gets fun.



## Building make: through the looking glass

Let's start from the beginning. As demonstrated above, we need some way to build tools like curl using make, and we need to build make to do that. But make isn't even the only example of this. In order to start building many of these tools, we need to start with more and more increasingly core build tools, and we need to ensure they're all built in a secure, transparent, repeatable way.



To solve this chicken-and-egg problem, we start by depending on packages built by Alpine. Alpine is a reliable, security-focused OS, which fits well for our purposes because it uses the same apk package format, and integrates easily with Melange. It's almost like we planned it that way… 😀



## Bootstrap Stage 1

The Stage 1 repo is here:[https://github.com/wolfi-dev/bootstrap-stage1](https://github.com/wolfi-dev/bootstrap-stage1)



Stage 1 builds a very small number of core packages, like gcc and glibc, using tools and libraries provided by Alpine. These are cross-compiled from Alpine's musl libc, and use [Alpine's set of CA certificates](https://github.com/wolfi-dev/bootstrap-stage1/blob/ce05b868a735f14405b1eb75bd09808978153472/cross-gcc.yaml#L26)to establish trustworthy HTTPS connections to source repositories.



The goal of Stage 1 is not to produce a broadly usable set of packages, only to build the bare minimum that we need to build the next stage.



## Bootstrap Stage 2

The Stage 2 repo is here:[https://github.com/wolfi-dev/bootstrap-stage2](https://github.com/wolfi-dev/bootstrap-stage2)



With the bare minimum packages built during Stage 1, we can begin to branch out to build more packages in Stage 2.



Stage 2 still depends on lots of packages provided by Alpine. Alpine's CA certificates previously used in Stage 1 are [repackaged into Stage 2's CA certificates package](https://github.com/wolfi-dev/bootstrap-stage2/blob/main/ca-certificates.yaml). Alpine's Perl is used to help [build Stage 2's busybox package](https://github.com/wolfi-dev/bootstrap-stage2/blob/main/busybox.yaml).



But with the small core of packages built for Wolfi in Stage 1, we can actually start to build quite a few useful packages, like [busybox](https://github.com/wolfi-dev/bootstrap-stage2/blob/main/busybox.yaml),[gzip](https://github.com/wolfi-dev/bootstrap-stage2/blob/main/gzip.yaml),[openssl](https://github.com/wolfi-dev/bootstrap-stage2/blob/main/openssl.yaml),[sed](https://github.com/wolfi-dev/bootstrap-stage2/blob/main/sed.yaml)and [wget](https://github.com/wolfi-dev/bootstrap-stage2/blob/main/wget.yaml).



Stage 2 also rebuilds the same packages provided by Stage 1, like [gcc](https://github.com/wolfi-dev/bootstrap-stage2/blob/main/gcc.yaml), so that future stages don't have to depend on Stage 1 packages anymore. Stage 1 has served its purpose at this point.



As with Stage 1, the purpose of Stage 2 is not to produce a useful set of packages for everyday use, it's just to give us the necessary boost to get to Stage 3.



## Bootstrap Stage 3

The Stage 3 repo is here:[https://github.com/wolfi-dev/bootstrap-stage3](https://github.com/wolfi-dev/bootstrap-stage3)



Stage 3 is where it starts to get fun. As with Stage 2, we'll start to build a few more packages than the previous stage, using packages provided by the previous stage. Unlike Stage 2, Stage 3 has no remaining dependencies on Alpine packages. We're almost there!



The goal of Stage 3 is to produce a minimal set of packages built using only packages built by Wolfi. To do this, it follows in the footsteps of Stages 1 and 2, and builds its set of packages, this time only depending on packages built during Stage 2. It rebuilds all the same packages built for Stages 1 and 2 in this way, and a few more that we'll need later.



As with previous stages, the purpose of Stage 3 is*still*not to produce a useful set of packages for everyday use, yet. But with Stage 3 packages built, we now have a solid foundation we can use to build any other packages we want.



## Looking Back

I think it's worth pausing here to reflect on what we've seen here, and why we've gone to all this trouble. We have a set of packages built completely from upstream source, purely using Wolfi's build processes, with build config and build metadata and logs transparently available for all to see in GitHub. You can see in the repos exactly which Alpine-built packages were used in Stages 1 and 2, and exactly which Wolfi-built packages were used in Stages 2 and 3. You can rebuild all those stages yourself, to produce the same set of bootstrap packages if you want.

![A diagram depicting how Wolfi was built from the ground up, with the help of Alpine.](blog-images/wolfi-arm64-diagram.png)

This is critical, because we don't just want to produce a set of packages and just pinky promise they were built securely. Don't just take our word for it, you can build it yourself and audit it if you want! All the way back to the beginning of the universe, with the minimal set of packages built from Alpine, another trustworthy distribution.



## Off to the races!

With Stage 3 complete, we're ready to start churning out secure packages. That's where the [main wolfi-dev/os repo](https://github.com/wolfi-dev/os)comes in.



The packages in the "real" Wolfi OS repo are built using packages from Stage 3, mainly using busybox, wget and CA certificates, and build tools like gcc and make. But the "real" OS repo also rebuilds these tools again from source, just so there's no confusion. These packages are the ones intended for wide usage by Wolfi users.



With the minimal set of bootstrapped packages available, we can start to build almost anything. Wolfi uses the bootstrapped packages to build packages for [OpenJDK](https://github.com/wolfi-dev/os/blob/main/openjdk-17.yaml),[Ruby](https://github.com/wolfi-dev/os/blob/main/ruby-3.1.yaml), NodeJS, Python,[Bazel](https://github.com/wolfi-dev/os/blob/main/bazel-5.yaml), Envoy, Nginx, RabbitMQ, Redis,[Memcached](https://github.com/wolfi-dev/os/blob/main/memcached.yaml), MariaDB, PostgreSQL,[sqlite](https://github.com/wolfi-dev/os/blob/main/sqlite.yaml), and anything else you might need. If there's anything you can't find,[let us know](https://github.com/wolfi-dev/os/issues/new?assignees=kaniini&labels=wolfi-package-request%2Cneeds-triage&template=new-wolfi-package-request.yml&title=%5BWolfi+Package+Request%5D%3A+%24PACKAGE_NAME)and we'll get to work adding it.



There's one more interesting thing to call out here: in keeping with the Go team's recommendation, Wolfi first fetches a Go toolchain pre-built by the Go team, then uses that to build the Go toolchain from source. Like the previous bootstrap packages, the so-called "go-stage0" package isn't meant to do anything but build the "real" Go package. Wolfi does the same thing for Rust too – use a [pre-built Rust toolchain](https://github.com/wolfi-dev/os/blob/main/rust-stage0.yaml)to build the Rust toolchain from source. The built-from-source Rust toolchain is the one Wolfi users use, and rust-stage0 is just there to show our work.



## Chainguard Images: Putting it all together

With all these packages built reliably and transparently from upstream source, Chainguard uses a separate tool,[apko](https://github.com/chainguard-dev/apko), to produce our [Chainguard Images](https://github.com/chainguard-images), ready to be used as a base image for your applications, or in your build pipelines. Like Wolfi OS packages, Chainguard Images are also built transparently with configs and build logs available on GitHub.



Since we maintain control of and visibility into the entire build process from upstream source to package to container image, and of all the build tools used to build the packages, we have unprecedented visibility into how the packages are built and maintained, and maximum control over how quickly security fixes are applied and released. This is a massive leap forward ahead of other distroless images, like [GCP's distroless](https://github.com/GoogleContainerTools/distroless), which use Bazel to package existing upstream Debian packages and have no direct control over the provenance or release cadence of those packages.

Aside from letting us apply security patches faster, building from source also lets us enable other features at build-time, like [enabling yjit in Ruby 3](https://www.chainguard.dev/unchained/chainguard-image-now-available-for-ruby-3-2).



If this sounds interesting to you, give Chainguard Images a try! If you need a custom base image containing whatever packages you need, built from upstream source and rebuilt with security fixes as soon as humanly possible,[reach out](https://www.chainguard.dev/get-demo), we'd love to help you.



## …You mentioned arm64?

Oh yeah! The reason this bootstrapping process is at the top of our mind lately is because we recently finished going through it again to rebuild all packages for 64-bit Arm support!



All of the bootstrapping stages described above were built in order, on [GKE Arm nodes](https://cloud.google.com/kubernetes-engine/docs/concepts/arm-on-gke), to produce arm64/aarch64 packages, using the same build configs in the bootstrapping repos, and with logs and metadata available in GitHub Actions.



With Arm packages built, we can start to provide multi-platform Chainguard Images with support for Arm container runtime environments, like those available on all three major clouds,[AWS](https://aws.amazon.com/ec2/graviton/),[GCP](https://cloud.google.com/compute/docs/instances/arm-on-compute)and [Azure](https://azure.microsoft.com/en-us/updates/public-preview-arm64based-azure-vms-can-deliver-up-to-50-better-priceperformance/), so you can take advantage of Arm's power consumption and cost benefits. Our hope is that, armed with this new feature, we can work arm in arm with our customers to optimize their cloud deployments, so they don't cost an arm and a leg.



Humerus puns aside, we'll continue to expand our set of available architectures in the new year, while we also expand the set of packages available in those architectures. Our hope is that Wolfi becomes the most trusted distro for your containerized workloads in 2023.
Share