# Go Things I Like: `testscript` and `txtar`

Jason Hall<br>
_First published TODO_

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

While building and thoroughly testing `go`, the Go team also incidentally invented a simple [DSL](https://en.wikipedia.org/wiki/Domain-specific_language) to express test scenarios, in the [`internal/script`](https://github.com/golang/go/blob/78b43037dc20b9f5d624260b50e15bfa8956e4d5/src/cmd/internal/script/engine.go) directory. They presumably kept it safely nestled away in `internal` so they wouldn't get bogged down with maintaining any kind of backward compatibility contracts -- if they wanted to make a breaking change to the behavior or syntax of the `script` language, they'd be the only consumer to worry about.





