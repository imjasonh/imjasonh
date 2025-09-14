*Original URL: https://www.chainguard.dev/unchained/how-chainguard-fixes-vulnerabilities*

---

# How Chainguard fixes vulnerabilities before they&#x27;re detected

*Jason Hall*

*July 14, 2023*

On July 11, Go released a security fix in 1.20.6 and 1.19.11. The central security issue was [CVE-2023-[29406](https://nvd.nist.gov/vuln/detail/CVE-2023-29406), where the standard library's net/http client didn't sufficiently sanitize and validate the Host header before sending the request. To quote the [ssue](https://github.com/golang/go/issues/60374):


*"A maliciously-crafted Host field can inject request headers or entire new requests into the sent request. For example, setting Request.Host to "hostname\r\n X-Header: oops" adds an X-Header: oops header to the request."*


All in all the issue itself isn't that bad – you can avoid it completely by not making HTTP requests based on arbitrary input, which is pretty uncommon. If you need to do that, you can mitigate it completely by sanitizing and validating user inputs, which is a good idea anyway. Seriously, try it out.


So why am I writing a blog post about this, and why are you reading it? Good question. We can both stop whenever we want…


But in all seriousness, I thought it would be interesting to talk about this issue not because the vulnerability is particularly bad, or its mitigation particularly interesting, but because it shows how fast [Wolfi](https://www.chainguard.dev/unchained/introducing-wolfi-the-first-linux-un-distro), our community distro, can be when packaging and releasing these fixes.


As a minor spoiler, at the time of writing this, all Go applications packaged by Wolfi contain the fix for this vulnerability, but even if they didn't, no scanner would have the information needed to detect and report it. Meaning, our patch is available***before***scanners could tell you about it.


*How does that even work?! I'm glad you asked.*


First, let's talk about how we got the fix out so fast. The answer is, we automated most of it.


In the Wolfi repo we run a bot that watches upstream projects for new releases. It watches the Go project, and hundreds of other projects. When Go released 1.20.6, wolfibot opened a [PR](https://github.com/wolfi-dev/os/pull/3531) to build the Go package from that new release. When the PR was opened we tested that it worked, the team reviewed the change and merged the PR, causing the updated 1.20.6 Go package to be released a few minutes later. The next day our [Go](https://edu.chainguard.dev/chainguard/chainguard-images/reference/go/overview/) image (cgr.dev/chainguard/go:latest) was rebuilt to include the latest version, and any application built using that version of the image would have the fix.


But that's just the Go image. At the time of writing this, Wolfi also has 192 packages built using Go, and since the vulnerability was in the Go standard library, those packages needed the fix too. So we sent nother [PR](https://github.com/wolfi-dev/os/pull/3549) to tell Wolfi to rebuild all of those packages with the latest Go we just built. A few hours later, 192 new packages rolled off the assembly line, free from the scourge of CVE-2023-29406. Shortly after, images containing those packages were rebuilt with the fix, ready to be pulled by anybody and everybody.


Every user of our [cert-[anager](https://edu.chainguard.dev/chainguard/chainguard-images/reference/cert-manager-controller/overview/), [tcd](https://edu.chainguard.dev/chainguard/chainguard-images/reference/etcd/overview/), [atekeeper](https://edu.chainguard.dev/chainguard/chainguard-images/reference/gatekeeper/overview/), [eda](https://edu.chainguard.dev/chainguard/chainguard-images/reference/keda/overview), [kubernetes-csi-node-driver-[egistrar](https://edu.chainguard.dev/chainguard/chainguard-images/reference/kubernetes-csi-node-driver-registrar/overview), [ulumi](https://edu.chainguard.dev/chainguard/chainguard-images/reference/pulumi/overview), [erraform](https://edu.chainguard.dev/chainguard/chainguard-images/reference/terraform/overview), and [asmer](https://edu.chainguard.dev/chainguard/chainguard-images/reference/wasmer/overview) images could sleep a little better at night knowing there's a fresh new image waiting for them.


Meanwhile, what were scanners up to? Good question. Mainly, they were completely unaware that CVE-2023-29406 even existed.


The main source of vulnerability that most scanners rely on is NVD, which at the time of writing this has not published a [CPE](https://en.wikipedia.org/wiki/Common_Platform_Enumeration) for the vulnerability. A [CVSS](https://en.wikipedia.org/wiki/Common_Vulnerability_Scoring_System) score hasn't been determined yet, saying what its severity is. Without this information, scanners that rely on NVD can't effectively identify the issue in artifacts that they scan. Your code may be affected, and you might not even be able to tell. This isn't NVD's fault, the vulnerability is just very very new!


Go's own [ovulncheck](https://pkg.go.dev/golang.org/x/vuln/cmd/govulncheck) reports the issue, because it uses Go's own vulnerability database, which tracks this [issue](https://pkg.go.dev/vuln/GO-2023-1878). The Go team has really advanced the state of the art on tracking and reporting vulnerabilities in its ecosystem, but unfortunately most scanners don't consult the Go vulnerability database yet.


Even if scanners could identify the vulnerability from NVD data, because it was in the Go standard library itself, most scanners wouldn't have reported it anyway – most scanners only report vulnerabilities detected in third-party Go modules and ecosystem packages.


To be clear, it's unlikely that most applications were actually sending requests based on arbitrary user input such that they would be vulnerable in the first place. But since most scanners wouldn't be able to tell you, you'd have to do a full audit of your code to be sure. For third-party dependencies, you'd have to wait for them to rebuild and release using the latest Go version, and for that upstream release to make its way to you through your distro.


Or you can use the newly built [Chainguard Image](https://www.chainguard.dev/chainguard-images) that had the fix before the scanners could even clock it.


Is your organization drowning in a backlog of vulnerability findings? Do you dream of being able to remediate vulns*******before*******scanners can even tell you about them? [Let's [alk](https://go.chainguard.dev/43paXim).
Share