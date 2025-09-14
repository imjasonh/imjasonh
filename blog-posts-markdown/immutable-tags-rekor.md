# Transparently immutable tags using Sigstore&#x27;s Rekor

*Jason Hall*

*July 7, 2022*

A lot of ink has been spilled on the immutable and sometimes-mutable nature of container images. In some ways, it's really the perfect topic for hot takes and sometimes-dubious best practices. I'd like to spill some more ink, and introduce a novel solution to the problem, taking advantage of [Sigstore](https://sigstore.dev/)'s [Rekor](https://docs.sigstore.dev/rekor/overview)transparency log.



The sometimes-mutable nature of container images is especially relevant when consuming public images, for example base images like`alpine`](https://hub.docker.com/_/alpine),[distroless](https://github.com/distroless)base images, or`debian`](https://hub.docker.com/_/debian). These are*very*widely used images, pulled millions of times each day by tens of thousands of organizations. As such, any changes to them can immediately impact lots of applications. You'd really like to be able to know*exactly*what's in these images, and know that what was in it yesterday will still be in it tomorrow.



To solve this, the container ecosystem has relied on content-addressed image references, which rely on a foundation of strong cryptographic principles to generate a unique identifier for the image based on the exact contents of the image. If one bit is changed anywhere in the image, its digest changes, representing a completely new image.



And this works great! But that strong cryptographic guarantee requires passing around long opaque strings like`registry.example.biz/my-app@sha256:d53768db04b3b2cef0965675a7eadcca0f8caeb8a1d458ad4544c2b39ffa0b99`which gets cumbersome fast. These references may be great for computers, but it's not easy for us humans, with our weak human brains, to tell what that long weird string*means*.

Is`sha256:d53768db04b3b2cef0965675a7eadcca0f8caeb8a1d458ad4544c2b39ffa0b99`newer or later than`sha256:b975637caf9be61ad6ad27c1cbb1f5ad82fcdea92c18389137877b4c44a426e4`?

How are`sha256:d53768db04b3b2cef0965675a7eadcca0f8caeb8a1d458ad4544c2b39ffa0b99`and`sha256:d53768db04b3b2cef0955675a7eadcca0f8caeb8a1d458ad4544c2bh9ffa0b99`different?*Are*they different? 🤷



## Image Tags

The classic solution to this problem is to apply tags to images. Tags are human-meaningful strings like`:v1.2.3`or`:202200705`, or a commit reference like`:e3b0f6`, or the ubiquitous`:latest`. These tags make it possible for human users to push and pull`registry.example.biz/my-app:v1.2.3`and have a reasonable level of confidence that the contents are version`1.2.3`of their application. The semantics of the version tag also help humans understand, or at least*assume*, that`:v1.2.4`is newer, and give a hint about roughly*how*different it is than`:v1.2.3`.



And this works, more or less, so long as you trust users not to update those tags to point to something else. Or accidentally make a typo. Or have their credentials stolen by an attacker. Oh and you also have to extend this trust to all the systems and human operators running the registry service.



Here at Chainguard, when it comes to ensuring the integrity of our software supply chains, we're not in the business of having just a*reasonable*level of confidence. Hope is famously not a strategy. There has to be a better way.



## Immutable Image Tags

Another approach to this problem has been*immutable tags*.



Some registry implementations, such as [Amazon's Elastic Container Registry](https://aws.amazon.com/ecr/), allow users to configure their image repositories to enable [immutable tags](https://docs.aws.amazon.com/AmazonECR/latest/userguide/image-tag-mutability.html). In this scenario, only repo administrators can enable immutable tags, and only administrators can make tags re-mutable. While the repo has immutable tags enabled, users can only push new tags, and are blocked from updating existing tags.



It's like one of those plastic covers over a big scary button you don't want to push by accident – in this case, the button says "update`:v1.2.3`".

![A red emergency stop button](../blog-images/immutable_tags_rekor_img1.jpeg)

Resist the urge to push the button.

And this works, more or less, so long as you trust your administrators not to forget to enable immutable tags on a new repo. Or make the repo mutable during maintenance and forget to flip it back. Or have their credentials stolen by an attacker. Oh and you also have to extend this trust to all the systems and human operators running the registry service.



Here at Chainguard, when it comes to ensuring the integrity of our software supply chains, we're not in the business of trusting puny human administrators not to mess up. To err is human. There has to be a better way.



## Transparently Immutable Tags

Rather than trusting human users administrators, we can rely on*transparency.*Specifically, we can rely on Sigstore's [Rekor](https://docs.sigstore.dev/rekor/overview)transparency log, which holds an append-only log of signed attestations about code artifacts. Every entry in Rekor is publicly readable, and holds a cryptographic reference to all previous entries, so any modification to any previous entry would be easily and immediately tamper-evident. Because it's public, anybody can run a [monitor](https://github.com/sigstore/rekor-monitor)to periodically check for bad entries, and alert on any inconsistencies.



Traditionally, Rekor has been used to store signatures and information about how artifacts were built, by whom, and what humans and systems attest to that. But Rekor is very flexible, and we can also use it to store attestations about what we've seen in the past, like what image tags point to what image contents.



Enter ✨**tlogistry**✨ – a public registry image proxy that collects tag history and stores it transparently in Rekor.



When you request an image by tag from tlogistry, such as`tlogistry.dev/alpine:3.16.0`, the registry will look up the requested public image from the real registry (DockerHub in this case), and consult Rekor to see if it's previously seen this image by tag. If it hasn't, it will append a new entry noting the tag and immutable digest. The Rekor entry is keylessly signed by a short-lived certificate obtained from [Fulcio](https://docs.sigstore.dev/fulcio/overview), Sigstore's code signing certificate authority. For more about Fulcio,[see our deep dive](https://blog.chainguard.dev/a-fulcio-deep-dive/).



The next time you pull that image by tag, tlogistry will find that entry in Rekor, ensure that entry was previously signed by itself, and block any requests for that image by tag that don't match the previous digest.



## Demo

First, build and push an image using`docker`:

```
`$ docker buildx build -t my-user/my-app:v1.2.3 -f Dockerfile . --push
 => => writing image sha256:c8995b6f891d3fab4c13a9f6675167dd5ef8fef08eac360d52480cb8a0a7cee9
 => => naming to my-user/my-app:v1.2.3
 => pushing my-user/my-app:v1.2.3 with docker`
```

Pull it through tlogistry:

```
`$ docker pull tlogistry.dev/my-user/my-app:v1.2.3
v1.2.4: Pulling from my-user/my-app
Digest: sha256:c8995b6f891d3fab4c13a9f6675167dd5ef8fef08eac360d52480cb8a0a7cee9
Status: Image is up to date for tlogistry.dev/my-user/my-app:v1.2.3
tlogistry.dev/my-user/my-app:v1.2.3`
```

(Note that the digest of the image we pulled matches the digest of the image we pushed.) Build and push again, ⚠️ updating the tag️ ⚠️:

```
`$ docker buildx build -t my-user/my-app:v1.2.3 -f Dockerfile.bad . --push
 => => writing image sha256:22ef1bcbbadd60c294749edf96f1a9570c96c86f4eb2023ed739c72266a63c5c
 => => naming to my-user/my-app:v1.2.3
 => pushing my-user/my-app:v1.2.3 with docker`
```

Pull it again through tlogistry, which fails because the tag changed! 💥

```
`$ docker pull tlogistry.dev/my-user/my-app:v1.2.3
Error response from daemon: tag invalid: tag "my-user/my-app:v1.2.3" mismatch;
got "sha256:22ef1bcbbadd60c294749edf96f1a9570c96c86f4eb2023ed739c72266a63c5c",
want "sha256:c8995b6f891d3fab4c13a9f6675167dd5ef8fef08eac360d52480cb8a0a7cee9"`
```

Because the source of truth is a publicly auditable, append-only transparency log, any user can query Rekor to see what tags tlogistry has already seen, and what digests they point to. Because tlogistry can*only*block updated tags, there's no trusting human administrator with access to enable/disable/re-enable it.



To opt in to using tlogistry, simply update your public image references to add the`tlogistry.dev/`prefix:

Public Image

Transparently Immutable Public Image

`alpine:3.16.0`

`tlogistry.dev/alpine:3.16.0`

`debian:bullseye-20220622`

`tlogistry.dev/debian:bullseye-20220622`

`ghcr.io/distroless/static:20220707`

`tlogistry.dev/ghcr.io/distroless/static:20220707`

When you pull through tlogistry, image contents are still served directly from the original public registry, and container image data is never stored by tlogistry. Requests for image manifests by digest are unaffected. Only public images are supported.



When tlogistry serves an image manifest by tag, the HTTP response will include additional headers describing where exactly that information can be found in Rekor:

```
`Tlog-Integratedtime: 2022-06-28T13:30:02Z
Tlog-Logindex: 2787137
Tlog-Uuid: 362f8ecba72f4326ec44bdec24f7cb2eef2b125e6390590bcaf6268d9b3833e0096381a1c2508eb2
Tlog-First-Seen: true`
```

Using this information, you can look up the entry in Rekor – for example,[this is an entry](https://rekor.tlog.dev/?uuid=362f8ecba72f4326ec44bdec24f7cb2eef2b125e6390590bcaf6268d9b3833e0096381a1c2508eb2)that records that the digest for`alpine:3.16.0`is`sha256:686d8c9dfa6f3ccfc8230bc3178d23f84eeaf7e457f36f271ab1acc53015037c`.

tlogistry is an experiment to demonstrate that transparency logs like Rekor can be used for more than just signing and attesting artifacts at build-time, and can be used to secure more stages of the software supply chain, even if the software's originators don't use Sigstore or Rekor. If this has inspired you to take advantage of Rekor in new and interesting ways, we'd love to hear about them!



The source for tlogistry is available on [GitHub](https://github.com/chainguard-dev/tlogistry), and includes a Terraform script to build and deploy your own instance to Google Cloud Run, in your own project.
Share