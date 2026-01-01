# Go Things I Like: `testscript`

http://articles.imjasonh.com/go-things-testscript.md<br>
Jason Hall<br>
_First published January 1, 2026_

-----

When writing a program that deals with user input, or that deals with files -- which is lots of programs! -- it's often useful to write integration tests that cover various cases of inputs and expected outputs.

As an example, let's say you're writing a CLI calculator app, that takes some expression as an argument, evaluates it, and prints the result:

```
$ go run ./cmd/calc "2+3"
5
```

How it accomplishes this isn't important. Maybe it asks an LLM. But if you're going to write a CLI calculator app, you need to test its basic functionality, and that means writing an integration test.

One way you might test this is by having a traditional Go table-driven test, that takes inputs and outputs:

```go
func TestCalculator(t *testing.T) {
  for _, c := range []struct{
    desc string
    expr string
    got  string
  } {{
    desc: "simple math",
    expr: "2+3",
    got:  "5",
  }, {
    //...etc...
  }} {
    t.Run(c.desc, func(t *testing.T) {
      got, err := calc(c.expr)
      if err != nil {
        t.Fatalf("calc(%q): %v", c.expr, err)
      }
      if got != c.want {
        t.Fatalf("calc(%q): got %q, want %q", got, c.want)
      }
    })
  }
}
```

You may also have a set of tests to cover invalid input, corner cases, more complex expressions, and so on.

This works, but eventually you start to get potentially dozens, even hundreds of test cases as your expression engine becomes more complex.

Maybe eventually you add support for reading complex expressions in `.math` files, and let users define their own functions, and modules, and plug-ins.

Before long, your once-simple table-driven test has gotten entirely out of hand. Your test case `struct` could have fields to describe a complex file layout, regexp matchers for output, probably all kinds of command-line flags and envs to control more complicated behavior.

Does this sound familiar? Because it definitely sounds familiar to me.

Well, wouldn't you believe it, but you and I aren't the first people to experience this pain, and even more importantly, we're not the _smartest_ people to experience this pain.

The reason I know that is because the Go team has experienced this since basically forever, and came up with a pretty great way to solve this complexity problem.

In addition to being a compiler, and a batteries-included standard library, `go` is also a CLI, that regularly interacts with files, any many various complicated environments. No matter how complicated our `calc` program gets, it almost certainly won't need as many tests as the `go` tool.

While building and thoroughly testing `go`, the Go team also incidentally invented a simple [domain-specific language](https://en.wikipedia.org/wiki/Domain-specific_language) to express test scenarios, in the [`internal/script`](https://github.com/golang/go/blob/78b43037dc20b9f5d624260b50e15bfa8956e4d5/src/cmd/internal/script/engine.go) directory. They presumably kept it safely nestled away in `internal` so they wouldn't get bogged down with maintaining any kind of backward compatibility contracts -- if they wanted to make a breaking change to the behavior or syntax of the `script` language, they'd be the only consumer to worry about.

`rogpeppe` later freed that package as part of his [`go-internal`](https://pkg.go.dev/github.com/rogpeppe/go-internal) repository. This means you can now write test scripts using the [`testscript`](https://pkg.go.dev/github.com/rogpeppe/go-internal/testscript) package.

This means that, in addition to the table-driven test above, we can also write a series of testscript files, and parse and execute them.

To crib from the testscript docs, you can write a Go test like this:

```go
func TestFoo(t *testing.T) {
	testscript.Run(t, testscript.Params{
		Dir: "testdata",
	})
}
```

...which loads all the `.txt` testscript files in `./testdata`, and parses and executes them. A test for our `calc` program might look like:

```
exec calc 2+3
stdout '5'
```

To make the `calc` program available to your test script environment, you can define a `Setup` func in your [`Params`](https://pkg.go.dev/github.com/rogpeppe/go-internal/testscript#Params) that builds the `calc` program.

Alternatively, you can define a custom `Cmd` that executes the `calc` codebase directly, without packaging it as a binary. To run this in your test you would just invoke the `calc` command's code directly, instead of `exec`:

```
calc 2+3
stdout '5'
```

Over time, these simple test scripts accrue in the codebase as simple `.txt` files in a `testdata` directory, where they can be given simple descriptive names. Each testscript file becomes its own Go sub-test case (i.e., a `t.Run`), so you can execute single testscript cases with:

```
go test cmd/go -run=TestFoo/^two_plus_three$`
```

Using `testscript` you can build up a large suite of pretty complicated integration tests, while retaining readability.

Common functionality can be refactored into more reusable `Cmds` which can get shared across tests.

This is not only useful to human maintainers -- AI agents have also proven very adept at writing and debugging tests in the simple testscript language, which naturally leads to more tests as you add functionality and find new corner cases.

### `testscript-rs`

I got so hooked on using `testscript` in my Go projects that I found myself wanting the same when I built Rust projects, so Claude and I ported `testscript` to Rust, which is available at https://crates.io/crates/testscript-rs

The featureset is intended to be as close as we could get to the Go version, and I wanted to provide an idiomatic Rust API, including better contextualized error messages and optional color output (not pictured below).

```
  4 |
  5 | exec echo "expected"
> 6 | stdout "actual"

Expected: 'actual'
  Actual: 'expected'
```

If you use `testscript-rs` and find bugs or inconsistencies with Go's `testscript`, or have ideas for UX improvements, please file an issue or send a PR!

Some functionality is still missing, but I've used it in a few small side projects and overall been very happy with the results.
