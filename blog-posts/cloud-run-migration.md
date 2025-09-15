*Original URL: https://www.chainguard.dev/unchained/migrating-chainguards-serving-infrastructure-to-cloud-run*

---

# Migrating Chainguard's Serving Infrastructure to Cloud Run
Jason Hall, Principal Software
 Engineer December 10, 2024

 Earlier this year, Chainguard quietly migrated its serving
 platform from Kubernetes to [Cloud Run](https://cloud.google.com/run). As far as we can tell, nobody
 noticed a thing –*which is exactly how things like this are supposed to go!*–
 but as an engineer involved in the project I wanted to take a minute to show off the
 team's work, and share a peek behind the curtain.

## Chainguard on Kubernetes

 From its beginning, Chainguard ran on two regional GKE
 clusters, serving our OIDC issuer, gRPC APIs to serve the [Console UI](https://images.chainguard.dev) and [chainctl CLI](https://edu.chainguard.dev/chainguard/administration/how-to-install-chainctl/), datastore
 services, the Chainguard Registry frontend, our [webhook event delivery](https://edu.chainguard.dev/chainguard/administration/cloudevents/events-reference/) infrastructure, and a number of internal services. Since the early engineering team
 largely came from Google and was deeply involved with [Knative](https://knative.dev/docs/) from the early days, it seemed like
 a good fit to have a simple Knative-on-GKE stack. We built and deployed our Go
 services using [ko apply](https://ko.build/reference/ko_apply/) in GitHub Actions. We used [GCLB](https://cloud.google.com/load-balancing/) to front our public services, and used [Istio](https://istio.io/) to route traffic
 inside the cluster.

 Near the end of 2023, however, the cracks were starting to
 show.

 GKE's managed Kubernetes updates were smooth for the most
 part, and Knative updates weren't too toilsome, but it was more than nothing.

 Each engineer working on the serving infrastructure had a dev
 environment to mimic prod, to develop features, which meant many largely-unused GKE
 clusters that each required some care and feeding, and the cost of those unused
 resources was becoming *very *noticeable.

 The way we were operating Istio was too complex. Although
 Knative autoscaled services in response to traffic, node autoscaling was slower than
 we wanted, and that sometimes meant dropped requests and user-visible errors. We
 kept a larger pool of nodes to absorb traffic spikes, but that just meant increased
 costs, as we were running servers that weren't actually serving most of the
 time.

 Our traffic patterns were – and still are – very spiky, and
 the spikes are largely self-induced. As [we build more Chainguard
 Images](https://www.chainguard.dev/unchained/milestone-1-000-secure-container-images-and-over-100-work-years-saved), our image build process has become a large share of our
 traffic – pushing images, then pulling them to test and scan them – and we want to
 push and test and scan our images as quickly as we can. But in doing so, we stressed
 the serving infrastructure's ability to scale up quickly, and we would see
 errors, and so would external users. Our serving infrastructure was becoming a
 bottleneck, and we hate bottlenecks.

 We had two clusters for reliability, but we knew that
 we'd want more eventually, and we knew that operating more clusters would only
 increase the complexity and cost.

 We knew we needed to do better.

## Chainguard on Cloud Run

 In December 2023, at an engineering summit in Phoenix, the
 team decided to migrate off of Kubernetes, and on to Cloud Run. This was a natural
 fit for us, since Cloud Run adheres to the same container contract as Knative, and
 basically offers a cluster-less experience for Knative services.

 In early load tests, Cloud Run scale-ups were shown to be
 faster and more reliable than our GKE infrastructure. Some basic prototyping showed
 that we could relatively easily bring up our core services (OIDC, datastore, API and
 registry) on Cloud Run using the exact same code we used to deploy to Knative on
 GKE.

 We started rewriting our Knative Service YAML configs in
 Terraform, using the [ko Terraform provider](https://github.com/ko-build/terraform-provider-ko/) to build our images
 instead of the ko CLI. From there it was off to the races.

## The Power of Abstraction

 While scaffolding the initial prototype on Cloud Run, we
 quickly realized that there were common patterns we wanted to codify and reuse.

 We wanted to support a global footprint, and ensure that
 internal traffic didn't leave our VPC. We built a simple [networking module](https://github.com/chainguard-dev/terraform-infra-common/tree/main/modules/networking) to codify
 this, which acts as the foundation for the rest of our services, along with the [module to configure GCLB](https://github.com/chainguard-dev/terraform-infra-common/tree/main/modules/serverless-gclb).
 This module is also responsible for DNS records, and makes it easy to manage
 subdomains that route to public services.

 Cloud Run offers regional services, but didn't offer
 multi-regional services, so we built the equivalent of a multi-regional Cloud Run Go
 service and [encapsulated it in a Terraform
 module](https://github.com/chainguard-dev/terraform-infra-common/tree/main/modules/regional-go-service). In our module, services are private by default, and have to
 be explicitly allowed to send traffic out of the VPC to the public internet.
 Services can be configured to receive traffic directly from the internet, but in
 practice they're either private internal services, or only accept traffic from
 our global GCLB via a DNS subdomain. Today we run services in three regions, but
 adding a fourth, fifth, or sixth should be trivial for stateless services.

 Services are automatically configured with an Open Telemetry
 sidecar container to export metrics and traces to GCP, and are run with a Service
 Account with minimal permissions by default. Services that need to talk to other
 services can be easily authorized to do so explicitly, and services that need to
 touch GCP resources (Cloud SQL, KMS, Secrets, etc.) must be authorized explicitly as
 well.

 A number of our internal services were based on [Knative Eventing](https://knative.dev/docs/eventing/), which offered a great
 platform for triggering asynchronous work, where workers could scale up and down
 with requests. We built a Terraform module to encapsulate the [same](https://github.com/chainguard-dev/terraform-infra-common/tree/main/modules/cloudevent-trigger) [concepts](https://github.com/chainguard-dev/terraform-infra-common/tree/main/modules/cloudevent-broker) based on Cloud
 Pub/Sub, and multi-regional services could subscribe to particular events. This
 model also encapsulates authorization to publish and subscribe, so that only
 services explicitly allowed to publish events were authorized to do so.

 We have a module that encapsulates subscribing to a feed of
 events and [recording those events into
 BigQuery](https://github.com/chainguard-dev/terraform-infra-common/tree/main/modules/cloudevent-recorder), with authorization checks to ensure that only that
 module's components can write to those BigQuery tables. This lets us easily
 keep track of events flowing through the system, build dashboards, and even replay
 events if needed.

 With those basic building blocks in place, we built up a
 second serving stack of all of our multi-regional Cloud Run services, and slowly
 shifted traffic to it, until the GKE stack was unused and could be decommissioned.
 In April, we pulled the plug, and there was much celebration.

 Development environments in this model were also made a lot
 simpler. When a stack isn't receiving traffic – as most developer environments
 aren't most of the time – services scale to zero and cost nothing. There's
 no cluster or Knative controllers to update. Even our dev environments are globally
 available, because why not?

 But we weren't done!

 To help us observe all these relatively homogeneous global
 services, we built Terraform modules to make [building GCP dashboards
 easier](https://github.com/chainguard-dev/terraform-infra-common/tree/main/modules/dashboard), and encapsulated some standard [dashboards for multi-regional
 services](https://github.com/chainguard-dev/terraform-infra-common/tree/main/modules/dashboard/service) and [internal event receiver
 services](https://github.com/chainguard-dev/terraform-infra-common/tree/main/modules/dashboard/cloudevent-receiver), with built-in alerts for common errors. This has been a
 huge benefit to our observability, since any new metric or alert we add to the
 dashboard for one service gets added to every service's dashboard by default.
 Now there's no excuse not to have great monitoring for every service.

 We're heavy users of GitHub, for both the Wolfi distro
 and our Chainguard Images product. As we built more and more automation around PRs
 and workflows for these repositories, we naturally folded that into our Terraform
 modules as well. There's a module that [forwards GitHub webhook events into
 our Pub/Sub eventing system](https://github.com/chainguard-dev/terraform-infra-common/tree/main/modules/github-events), and event recorder, allowing us to
 easily monitor and record GitHub events in all our repos. We even built a [simple GitHub bot SDK](https://github.com/chainguard-dev/terraform-infra-common/tree/main/modules/github-bots) that
 encapsulates both the Terraform needed to bring up an event receiver, and a [small Go framework](https://pkg.go.dev/github.com/chainguard-dev/terraform-infra-common/modules/github-bots/sdk) to make
 it easier to write receiver bots. We now have dozens of bots running on our repos,
 checking for errors, suggesting fixes, and ensuring our packages are always
 up-to-date and CVE-free.

 There's also Terraform modules for [probers](https://github.com/chainguard-dev/terraform-infra-common/tree/main/modules/prober), and [cron jobs](https://github.com/chainguard-dev/terraform-infra-common/tree/main/modules/cron), and [secrets](https://github.com/chainguard-dev/terraform-infra-common/tree/main/modules/secret), and even a module
 for handling [workqueue](https://github.com/chainguard-dev/terraform-infra-common/tree/main/modules/workqueue) items, heavily
 inspired by Kubernetes controllers' workqueue infrastructure.

 Migrating to this pattern has given us lots of benefits.
 It's helped us standardize our security best practices, and optimize our
 observability and monitoring. When an engineer goes to start a new project, they
 don't have to think about how to build the services, they just create a new
 regional-go-service, hook it up to GCLB or the event broker, and they can get to
 work quickly.

 The Terraform modules we've built are shared as an open
 source example of how we've built our serving infrastructure over the last year
 (its [first birthday](https://github.com/chainguard-dev/terraform-infra-common/commit/90182645e3f20e61ee1cd5a13c601747ea4b800c) is today,
 December 10th!). However, we don't intend to operate that codebase as a
 community project – pull requests from external contributors are unlikely to get
 merged, especially if they add features we don't need, or compromise stability
 or security. You're more than welcome to fork the repo and use it however you
 want. Let us know how it goes!

 I hope this has been a fun peek into how we deliver our
 production services at Chainguard. If this sort of thing interests you, I should
 mention that we're planning to grow our engineering team, and are [looking for folks](https://chainguard.dev/careers) who read and get excited
 by blog posts like this. If you'd like to learn more, and maybe even *get
 paid *to learn more, I encourage you to reach out. 2024 was a very
 interesting year for our serving infrastructure, and 2025 is shaping up to be even
 more interesting!