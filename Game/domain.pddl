(define (domain blockmove)
  (:requirements :strips :typing)
  (:types loc direction block)
  (:predicates
    (at-player ?l - loc)
    (at ?b - block ?l - loc)
    (connected ?l1 ?l2 - loc ?d - direction)
    (clear ?l - loc)
    (is-hole ?l - loc)
    (stored ?b - block)
  )

  (:action move
    :parameters (?l1 ?l2 - loc ?d - direction)
    :precondition (and (at-player ?l1) (connected ?l1 ?l2 ?d) (clear ?l2))
    :effect (and (not (at-player ?l1)) (at-player ?l2) (clear ?l1) (not (clear ?l2)))
  )

  (:action push
    :parameters (?l1 ?l2 ?l3 - loc ?d - direction ?b - block)
    :precondition (and (at-player ?l1) (at ?b ?l2) (connected ?l1 ?l2 ?d) (connected ?l2 ?l3 ?d) (clear ?l3))
    :effect (and (not (at-player ?l1)) (at-player ?l2) (clear ?l1) (not (clear ?l2)) 
                 (not (at ?b ?l2)) (at ?b ?l3) (not (clear ?l3)))
  )

  (:action push-to-hole
    :parameters (?l1 ?l2 ?l3 - loc ?d - direction ?b - block)
    :precondition (and (at-player ?l1) (at ?b ?l2) (connected ?l1 ?l2 ?d) (connected ?l2 ?l3 ?d) (is-hole ?l3))
    :effect (and (not (at-player ?l1)) (at-player ?l2) (clear ?l1) (not (clear ?l2))
                 (not (at ?b ?l2)) (stored ?b))
  )
)
