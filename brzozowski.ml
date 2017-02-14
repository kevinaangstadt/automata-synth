(*http://cs.stackexchange.com/questions/2016/how-to-convert-finite-automata-to-regular-expressions*)
(*http://web.archive.org/web/20140922220310/http://codepad.org/dbFztCCM*)

type re = | Empty | Epsilon | Car of char | Union of re * re
	  | Concat of re * re | Star of re

let sprint_re =
  let rec s = function
    | Empty -> "0"
    | Epsilon -> "1"
    | Car c -> String.make 1 c
    | Union (e, f) -> s e ^ "+" ^ s f
    | Concat (e, f) -> "(" ^ s e ^ ")(" ^ s f ^ ")"
    | Star e -> "(" ^ s e ^ ")*"
  in s

let simple_re =
  let rec simple = function
    | Union (e, f) when e = f -> e
    | Union (Union (e, f), g) -> simple (Union (e, Union (f, g)))
    | Concat (Concat (e, f), g) -> simple (Concat (e, Concat (f, g)))
    | Concat (Epsilon, e) | Concat (e, Epsilon) -> simple e
    | Concat (Empty, e) | Concat (e, Empty) -> Empty
    | Union (Empty, e) | Union (e, Empty) -> e
    | Star Empty -> Epsilon
    | Star Epsilon -> Epsilon
    | Star e -> Star (simple e)
    | Union (e, f) -> Union (simple e, simple f)
    | Concat (e, f) -> Concat (simple e, simple f)
    | (Empty | Epsilon | Car _) as e -> e
  in
  let rec f e =
    let e' = simple e in
    if e = e' then  e' else f e'
  in f

let brzozowski a b =
  let m = Array.length a in
  for n = m-1 downto 0 do
    b.(n) <- Concat (Star a.(n).(n), b.(n));
    for j = 0 to n-1 do
      a.(n).(j) <- Concat (Star a.(n).(n), a.(n).(j));
    done;
    for i = 0 to n-1 do
      b.(i) <- Union (b.(i), Concat (a.(i).(n), b.(n)));
      for j = 0 to n-1 do
        a.(i).(j) <- Union (a.(i).(j), Concat (a.(i).(n), a.(n).(j)));
      done
    done;
    for i = 0 to n-1 do
      a.(i).(n) <- Empty;
    done;
  done;
  b.(0)

let a = [|
    [| Empty ; Car 'a' ; Car 'b' |];
    [| Car 'b' ; Empty ; Car 'a' |];
    [| Car 'a' ; Car 'b' ; Empty|];
  |]

let b = [| Epsilon ; Empty ; Empty |]

let () =
  let re = brzozowski a b in
  print_endline (sprint_re (simple_re re))