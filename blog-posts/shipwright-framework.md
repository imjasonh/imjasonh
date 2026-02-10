# Shipwright: A framework for building container images on Kubernetes

**Jason Hall**

*June 17, 2021*

---

As the popularity of [container](https://developers.redhat.com/topics/containers/) orchestration systems like [Kubernetes](https://developers.redhat.com/topics/kubernetes/) has exploded, we've seen two trends begin to emerge:

- Developers are seeking a reliable, secure system to build container images.
- Operators are looking for alternatives to managing and securing a separate build infrastructure.

The container ecosystem explosion began with developers running `docker build` and `docker push` on their local machines. But increasingly, developers have discovered the benefits of building container images remotely in the cloud, such as better automation, supply chain security, visibility and observability, increased efficiency from caching, and more.

With supply chain security becoming a hot topic in 2021, operators don't want to manage *and secure* a separate bespoke build infrastructure. In the past, this "build infrastructure" has sometimes been as simple as a shared computer running under a developer's desk. However, that build environment was difficult to manage, upgrade, and secure. Furthermore, often, it ran with very privileged access to production environments, making it a prime target for attackers.

Instead, operators want to lean on the tools and experience they've gained to secure and observe their production environments running on Kubernetes. Moving container image builds into the cluster is a natural fit, but running `docker build` in a cluster can be very hard to secure properly.

To meet this need, engineers from the [Red Hat OpenShift](https://developers.redhat.com/products/openshift/overview) build and [IBM Cloud Code Engine](https://www.ibm.com/cloud/code-engine) teams developed [Shipwright](http://shipwright.io).

## Build container images with Shipwright

Shipwright is a modern, flexible, secure framework for building container images on a Kubernetes cluster, using familiar Kubernetes-style APIs, and running workloads using [Tekton](http://tekton.dev).

Shipwright lets you take advantage of an array of modern container build tools like [Cloud Native Buildpacks](http://buildpacks.io), [Kaniko](http://github.com/googlecontainertools/kaniko), [Buildah](https://buildah.io/), [Source-to-Image (S2I)](https://github.com/openshift/source-to-image), [BuildKit](https://docs.docker.com/develop/develop-images/build_enhancements/), and [ko](https://github.com/ko-build/ko), and is flexible enough to quickly adapt to whatever new tools come along in the future.

Shipwright already powers IBM Cloud Code Engine's build system and will form the basis for Red Hat OpenShift builds version 2, which is expected to be launched in technical preview later this year. Shipwright is [being proposed](https://github.com/cdfoundation/toc/pull/95) as an incubating project under the [Continuous Delivery Foundation](http://cd.foundation), a Linux Foundation initiative that provides a neutral home for modern [continuous delivery](https://developers.redhat.com/topics/ci-cd/) projects of all kinds.

## Learn more

For more information about Shipwright, join us at [cdCon](https://events.linuxfoundation.org/cdcon/) on Wednesday, June 23, for [Introduction to Shipwright](https://sched.co/iov0), where I'll present an overview of the project, and on Thursday, June 24, for [Project Shipwright in Depth](https://sched.co/jvor), where Adam Kaplan and Enrique Encalada will go into more detail.

Until then, you can find documentation at <https://shipwright.io> and find the code on [GitHub](http://github.com/shipwright-io/build). You can also check out the article [Project Shipwright and the future of Red Hat OpenShift builds](https://developers.redhat.com/articles/2021/06/14/project-shipwright-and-future-red-hat-openshift-builds#) on Red Hat Developer.
