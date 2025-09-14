# Move over, Dockerfiles! The new way to craft containers

*Jason Hall, Software Engineer and Zachary Newman*

*April 27, 2023*

Docker has become an immensely popular tool in the world of software development, and for good reason. It provides an excellent way to create, manage, and deploy containers, which in turn enables developers to run applications that work the same way in development and production. However, creating Docker images can sometimes be a pain, as anybody who has accidentally broken the apt cache and triggered an hours-long build by making a minor change can tell you.



The standard, Dockerfile approach to creating container images can cause:



- 

Security concerns. Dockerfiles make it hard to know what’s in a package. This often results in low-quality Software Bills of Materials (SBOMs). Build commands in Dockerfiles end up as metadata in the resulting image, which can leak secrets, as recently noted in this [Aqua Security report](https://blog.aquasec.com/250m-artifacts-exposed-via-misconfigured-registries). Running Docker is a privileged operation, which risks attacks on your build infrastructure.

- 

Performance issues. Dockerfiles might take a long time to build, and don’t effectively use caches by default.

- 

Bloated containers. Dockerfile containers can have extra files, which consume bandwidth and storage, and (worse) might introduce security vulnerabilities.

- 

Exposed build services. Common Dockerfile build patterns require internet access, meaning that build infrastructure heavily favors an online environment and non-hermetic builds.



In this blog post, we'll:



- 

Explore some issues with Dockerfiles.

- 

Look at some alternatives for crafting containers, like ko, Bazel, Nix, and apko, and see their strengths and weaknesses.

- 

See what these techniques have in common, and how you might choose and migrate to one that meets your needs.



## The Issue with Dockerfiles



A Dockerfile is effectively a shell script that runs to set up a container image. Consider this example, adapted from the [Docker Library buildpack-deps image](https://github.com/docker-library/buildpack-deps):

```
`FROM ubuntu
RUN set -eux;
	apt-get update;
	apt-get install -y --no-install-recommends \
		ca-certificates \
		curl \
	; \
	rm -rf /var/lib/apt/lists/*

COPY . /app
RUN make /app
CMD python /app/app.py`
```

This is easy to write, but hard to reason about. For instance, the`apt-get install`line needs to chain several commands together to follow the Dockerfile best practices and avoid leaving extra files in the final image.



Dockerfiles have a few well-known issues that can make them a less-than-ideal solution for crafting containers:



### **Non-hermetic**

A [hermetic build](https://bazel.build/basics/hermeticity)declares its inputs explicitly, which allows pre-fetching of inputs and builds that can run offline. Dockerfiles often contain implicit dependencies, because they fetch dependencies online at build time (without explicitly pinning an exact file hash). The internet changes constantly, as new packages are published or servers have outages. In our example, the exact packages installed will depend on the state of the Ubuntu package repository at the time the Docker build occurs.



Dockerfile builds*can*be made hermetic with a disciplined approach, but you'll always be fighting to detect and fix reproducibility regressions because that's not what the tool or Dockerfile spec wants to do; even the recommended “[best practices](https://docs.docker.com/develop/develop-images/dockerfile_best-practices/)” have hermeticity problems.



Ultimately, without hermeticity, a Docker image can’t be reproducible (which has problems for caching as well as verifiability). Further, builds will need to happen online—increasing the risk to the build infrastructure.



### **What’s in your image?**

Dockerfiles usually start with a base image, like Ubuntu, which comes with a lot of software. This may lead to hundreds of [vulnerabilities in your final image](https://chainguard.dev/blog-static/chainguard-all-about-that-base-image.pdf)due to software you don’t even care about. In many cases, these vulnerabilities are not exploitable, but it only takes one—and manually checking each can be a pain.



Further, Dockerfile builds can lead to [software dark matter](https://www.chainguard.dev/unchained/software-dark-matter-is-the-enemy-of-software-transparency), which are files with an unexplained source (for instance, those that don’t come from a package manager). These can be confusing to Software Composition Analysis (SCA) tools like [grype](https://github.com/anchore/grype),[snyk](https://github.com/snyk/cli), and [trivy](https://github.com/aquasecurity/trivy). In addition to vulnerabilities, these extra files can cause bloat, leading to larger image sizes and extra bandwidth and storage costs. Dockerfile-based builds can generate Software Bills of Materials (SBOMs), but these SBOMs miss many dependencies, even though [more information about the package is available at build-time](https://www.chainguard.dev/unchained/make-sboms-not-guessboms-why-we-need-to-shift-left-on-sbom-generation)than any point later on. Docker build tooling does [support creating build provenance attestations](https://docs.docker.com/build/attestations/), which can play a useful role in a [secure software supply chain](https://www.chainguard.dev/unchained/the-role-of-attestations-in-a-secure-software-supply-chain).



Even [Multistage Dockerfiles](https://docs.docker.com/build/building/multi-stage/), which can prevent build dependencies from ending up in the final image, have many of these same issues.



## Alternatives to Dockerfiles



### ko

[ko](https://github.com/ko-build/ko)is a CNCF project designed specifically for Go applications. To compile a Go app and place it directly into a container, a user simply runs ko build—in many cases, no configuration is required! This tool doesn't depend on Docker, which makes it faster, more reliable, and portable. It also produces reproducible images with Software Bills of Materials (SBOMs) by default and results in very minimal images.



When ko works for your application, it’s an incredible tool. But it only works for pure-Go applications; if your container needs another service, strange libraries, or CGO, you might be out of luck. There are ko-like projects for Java ([Jib](https://github.com/GoogleContainerTools/jib)) and .NET ([dotnet publish](https://learn.microsoft.com/en-us/dotnet/core/docker/publish-as-container)) as well, which share the same strengths and limitations.



### Bazel rules_oci



[rules_oci](https://github.com/bazel-contrib/rules_oci)(like its predecessor,[rules_docker](https://github.com/bazelbuild/rules_docker), created by Chainguard CTO Matt Moore) leverages Bazel, an open-source universal build tool. Users define their container image in a Bazel rule:

```
`oci_image(
 name = "image",
 architecture = select({
 "@platforms//cpu:arm64": "arm64",
 "@platforms//cpu:x86_64": "amd64",
 }),
 base = "@ubuntu",
 cmd = ["app.bash"],
 os = "linux",
 tars = [":app.tar"],
)`
```

If your application already builds in Bazel, it’s easy to pull the targets into the ultimate Docker image and configure it to run. And because it uses Bazel, it's fast (with good caching), reproducible, and can run across a large build cluster.



However, “If your application already builds in Bazel” is a big ask. While Bazel supports many programming languages with first-party integrations, and extensions allow it to use any language, Bazel can be a pain to run. It can work really well in enormous, really complex monorepos (like inside Google, where Bazel came from). But “partly-Bazel” codebases are difficult to manage, and the complexity of setting it up (especially when integrating with external software) can be overwhelming.



### Nix



Nix is a build tool that emphasizes reproducibility. It's based on academic theory, as described in Eelco Dolstra's [PhD thesis](https://edolstra.github.io/pubs/phd-thesis.pdf). Nix’s [dockerTools](https://nix.dev/tutorials/building-and-running-docker-images)library provides excellent support for building Docker images:



```
`let
 nginxConf = pkgs.writeText "nginx.conf" ''
 daemon off;
 '';
in pkgs.dockerTools.buildImage {
 contents = [ pkgs.nginx ];
 config = {
 Cmd = [ "nginx" "-c" nginxConf ];
 ExposedPorts = {
 "8080/tcp" = {};
 };
}`
```

Nix builds images using the Nix cache, ensuring that only runtime dependencies end up in the final image. The final image will always be bit-for-bit reproducible. If you have multiple related images, they can even share layers, reducing disk usage.



A related approach eschews dockerTools, instead running Nix itself inside of Docker to build the container image. This has some similar properties, but users use`docker build`instead of`nix`to build the image. Unfortunately, the final image is no longer reproducible when using this technique.



The primary downside to Nix is its steep learning curve and high cost of adoption. Docker builds in Nix are written using the Nix programming language. The Nix language is a full-blown programming language, not just a configuration format like YAML. Nix is lazy and functional, which can be confusing for anybody who doesn’t write Haskell on a daily basis. Nix can be pedantic: it differentiates between build-time tools producing build-time artifacts, build-time tools producing run-time artifacts, build-time tools producing run-time dependencies, and run-time dependencies themselves. Multiple attempts have been made to improve the learning curve with tools like [Flox](https://floxdev.com/)and [Fleek](https://getfleek.dev/), but none has caught on quite yet.



### apko



[apko](https://github.com/chainguard-dev/apko)is a build tool from Chainguard designed specifically for creating base images. It's what we use to produce all of our [Chainguard Images](https://www.chainguard.dev/chainguard-images), and it's instrumental in being able to effectively maintain so many high-quality images. apko uses the [APK package format](https://wiki.alpinelinux.org/wiki/Apk_spec)used by Alpine Linux, and follows a radical principle: all of the contents of the container image must come from APK packages. In practice, this isn’t a big constraint, as tooling like [melange](https://github.com/chainguard-dev/melange)makes it easy to create APKs.[Wolfi](https://wolfi.dev/)uses melange to build the thousands of packages it provides. But limiting image creation to assembling packages and configuring Docker metadata comes with huge benefits:



- 

Building is lightning fast.

- 

Images are reproducible.

- 

Builds are more secure and don't require any privileges: they work by downloading packages over HTTPS and assembling images, not executing any other commands.

- 

Images come with SBOMs that are complete.



Here’s a (lightly abridged) example of a configuration file for [an Nginx image](https://github.com/chainguard-dev/apko/blob/889f9c1ed2f3e94736dafc58a3f42c26f4eaf659/examples/nginx.yaml):

```
`contents:
 packages:
 - wolfi-baselayout
 - nginx

entrypoint:
 type: service-bundle
 services:
 nginx: /usr/sbin/nginx -c /etc/nginx/nginx.conf

paths:
 - path: /etc/nginx/http.d/default.conf
 type: hardlink
 source: /usr/share/nginx/http-default_server.conf`
```

We can see that apko is much simpler than something like Bazel or Nix: there’s no new programming language, just YAML (and the [full description of the configuration format](https://github.com/chainguard-dev/apko/blob/main/docs/apko_file.md)runs about 250 lines). In cases where apko itself isn’t a good fit, it can be used to create base images to be used with any of the tools described above,[even Dockerfile builds](https://edu.chainguard.dev/open-source/wolfi/wolfi-with-dockerfiles/).



## Conclusion



Declarative approaches to building containers, such as those provided by the alternatives mentioned above, offer several advantages over traditional Dockerfiles. They're generally faster, provide better caching, and result in more minimal images. They do involve learning and installing new software, which is a real cost.



So what should you do? The following guidance is appropriate in most cases:



- 

If you already use and love a build system like Bazel or Nix, use that ecosystem’s Docker tooling to get reproducible, hermetic builds.

- 

If your applications work with special-purpose tools like [ko](https://github.com/ko-build/ko),[Jib](https://github.com/GoogleContainerTools/jib), or [dotnet publish](https://learn.microsoft.com/en-us/dotnet/core/docker/publish-as-container/), use those.

- 

If you care about build speed, reproducibility, Software Bills of Materials (SBOMs) for your containers, and minimal images, consider [apko](https://github.com/chainguard-dev/apko).

- 

Otherwise, use Dockerfiles. Consider using base images that come from the above tools.



As software development evolves, it's important to consider new and improved ways to craft containers that address the limitations of Dockerfiles. By exploring alternative tools like Ko, Bazel rules_docker, Nix, and Apko, you can create more efficient, reliable, and secure container images for your applications.
Share