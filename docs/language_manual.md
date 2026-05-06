# PocketLang Language Manual

**CS4031 — Compiler Construction, Spring 2026**
**Version 1.0**

---

## 1. Introduction

PocketLang is a small, statically-scoped imperative language designed for teaching compiler construction. Programs are compiled to three-address code (TAC), optimised, and executed on a lightweight virtual machine.

Key properties:
- Dynamically typed at the value level (integers and floats only)
- Statically scoped — `func` blocks create a new scope
- No first-class functions; functions are declared at the top level or inside blocks
- Single-pass compilation; no forward references to functions

---

## 2. Lexical Structure

### 2.1 Character set
PocketLang source files are UTF-8 text. Only printable ASCII characters are meaningful; the rest are ignored.

### 2.2 Whitespace
Spaces, tabs, and newlines are token separators and are otherwise ignored.

### 2.3 Comments
Single-line comments begin with `//` and extend to the end of the line.

```
// This is a comment
let x = 42  // inline comment
```

### 2.4 Keywords
The following identifiers are reserved:

```
let   if   else   while   func   return   print
```

### 2.5 Identifiers
An identifier starts with a letter or underscore, followed by zero or more letters, digits, or underscores.

```
IDENT ::= [a-zA-Z_][a-zA-Z0-9_]*
```

### 2.6 Integer literals
A sequence of one or more decimal digits.

```
INT_LIT ::= [0-9]+
```

### 2.7 Floating-point literals
A decimal integer part, a dot, and a decimal fraction part (both parts required).

```
FLOAT_LIT ::= [0-9]+ '.' [0-9]+
```

### 2.8 Operators and punctuation

| Token   | Meaning                  |
|---------|--------------------------|
| `+`     | Addition                 |
| `-`     | Subtraction / unary neg  |
| `*`     | Multiplication           |
| `/`     | Division                 |
| `%`     | Modulo                   |
| `==`    | Equality                 |
| `!=`    | Inequality               |
| `<`     | Less than                |
| `>`     | Greater than             |
| `<=`    | Less-or-equal            |
| `>=`    | Greater-or-equal         |
| `=`     | Assignment (in `let`)    |
| `(`     | Open parenthesis         |
| `)`     | Close parenthesis        |
| `{`     | Open block               |
| `}`     | Close block              |
| `,`     | Argument separator       |

---

## 3. Types

PocketLang has two value types:

| Type    | Description                        | Example literal |
|---------|------------------------------------|-----------------|
| `int`   | 64-bit signed integer              | `42`, `0`, `-7` |
| `float` | 64-bit IEEE-754 double             | `3.14`, `0.5`   |

Type promotion rules:
- Any binary operation with at least one `float` operand yields `float`.
- Integer division truncates toward zero.
- Division or modulo by the literal `0` is a runtime error (not folded at compile time).

---

## 4. Expressions

Expressions are evaluated in the following precedence order (lowest to highest):

| Level       | Operators             | Associativity |
|-------------|-----------------------|---------------|
| Equality    | `==`  `!=`            | Left          |
| Comparison  | `<`  `>`  `<=`  `>=`  | Left          |
| Term        | `+`  `-`              | Left          |
| Factor      | `*`  `/`  `%`         | Left          |
| Unary       | `-` (negation)        | Right (prefix)|
| Primary     | literals, names, calls, `(expr)` | — |

Comparison and equality expressions evaluate to `1` (true) or `0` (false).

### 4.1 Primary expressions

```
primary = INT_LIT
        | FLOAT_LIT
        | IDENT
        | IDENT "(" [ expr { "," expr } ] ")"
        | "(" expression ")"
```

Variable reads: the identifier must have been declared with `let` in an enclosing scope, otherwise a semantic error is raised.

Function calls: the callee must have been declared with `func`; arity must match.

---

## 5. Statements

### 5.1 Variable declaration / update — `let`

```
let <name> = <expression>
```

Declares `<name>` in the current scope (or updates it if already declared in the same scope). There is no bare assignment statement; `let x = x + 1` is the idiom for an in-place update.

**Example:**
```
let x = 10
let x = x + 1   // x is now 11
```

### 5.2 Conditional — `if` / `else`

```
if <expression> { <statements> }
if <expression> { <statements> } else { <statements> }
```

The condition is any expression; a non-zero value is truthy, zero is falsy. The `else` branch is optional.

**Example:**
```
if x > 0 {
    print x
} else {
    print 0 - x
}
```

### 5.3 Loop — `while`

```
while <expression> { <statements> }
```

Evaluates the condition before each iteration. The body is skipped entirely if the condition is initially false.

**Example:**
```
let i = 0
while i < 10 {
    print i
    let i = i + 1
}
```

### 5.4 Function declaration — `func`

```
func <name> ( [<param> { , <param> }] ) { <statements> }
```

Functions may appear anywhere a statement is allowed. Parameters are local to the function body. Functions do not have explicit return types; a missing `return` exits with no value (the caller receives `None` internally, which prints as `None`).

**Example:**
```
func add(a, b) {
    return a + b
}
let result = add(3, 4)
print result
```

### 5.5 Return — `return`

```
return [ <expression> ]
```

Exits the current function. `return` outside a function body is a semantic error. An optional expression supplies the return value.

### 5.6 Print — `print`

```
print <expression>
```

Evaluates the expression and writes its value followed by a newline to standard output. This is the only output facility in PocketLang.

### 5.7 Block

```
{ <statements> }
```

A block introduces a new nested scope. Declarations inside are not visible outside.

### 5.8 Expression statement

Any expression may appear as a statement; its value is discarded. This is mainly useful for function calls with side effects.

```
add(1, 2)   // call for side effects; return value discarded
```

---

## 6. Scoping

PocketLang uses **lexical (static) scoping**. Each block (`{…}`) creates a child scope. Name lookup walks from the innermost scope outward and stops at the first match.

```
let x = 1
if 1 == 1 {
    let x = 2     // new x in inner scope
    print x       // prints 2
}
print x           // prints 1
```

Function parameters are local to the function body.

---

## 7. Error Reporting

All errors are printed to **stderr** in the format:

```
[Phase] file:line:col — message
    source line
    ^
```

Where `Phase` is one of `Lexer`, `Parser`, `Semantic`, or `Runtime`.

**Example:**
```
[Semantic] prog.pcalc:3:5 — 'z' is not declared
    let y = z + 1
            ^
```

---

## 8. Compiler Flags

Run programs via the CLI:

```
python3 pocketlang.py run <file.pcalc> [--no-opt] [--debug=<phase>]
```

| Flag            | Effect                                              |
|-----------------|-----------------------------------------------------|
| `--no-opt`      | Skip all optimisation passes                        |
| `--debug=tokens`| Print token stream from the lexer                  |
| `--debug=ast`   | Print the AST (pretty-printed)                      |
| `--debug=symtab`| Print the symbol table after semantic analysis      |
| `--debug=ir`    | Print raw TAC before optimisation                   |
| `--debug=opt`   | Print TAC before and after each optimisation pass   |
| `--debug=all`   | Enable all debug outputs                            |

---

## 9. Complete Example

```
// Fibonacci using recursion
func fib(n) {
    if n <= 1 {
        return n
    }
    return fib(n - 1) + fib(n - 2)
}

let i = 0
while i <= 10 {
    print fib(i)
    let i = i + 1
}
```

Expected output:
```
0
1
1
2
3
5
8
13
21
34
55
```

---

## 10. Grammar Summary (EBNF)

```ebnf
program      = { statement } ;

statement    = let_stmt | if_stmt | while_stmt | func_decl
             | return_stmt | print_stmt | expr_stmt | block ;

let_stmt     = "let" IDENT "=" expression ;
if_stmt      = "if" expression block [ "else" block ] ;
while_stmt   = "while" expression block ;
func_decl    = "func" IDENT "(" [ IDENT { "," IDENT } ] ")" block ;
return_stmt  = "return" [ expression ] ;
print_stmt   = "print" expression ;
block        = "{" { statement } "}" ;
expr_stmt    = expression ;

expression   = equality ;
equality     = comparison { ("=="|"!=") comparison } ;
comparison   = term       { ("<"|">"|"<="|">=") term } ;
term         = factor     { ("+"|"-") factor } ;
factor       = unary      { ("*"|"/"|"%") unary } ;
unary        = [ "-" ] primary ;
primary      = INT_LIT | FLOAT_LIT | IDENT | call | "(" expression ")" ;
call         = IDENT "(" [ expression { "," expression } ] ")" ;

INT_LIT      = [0-9]+ ;
FLOAT_LIT    = [0-9]+ "." [0-9]+ ;
IDENT        = [a-zA-Z_][a-zA-Z0-9_]* ;
```
