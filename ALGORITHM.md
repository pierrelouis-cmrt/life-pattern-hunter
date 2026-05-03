# Life Pattern Hunter Algorithm

This script searches for an initial Conway's Game of Life grid that becomes your chosen target grid after `X` steps.

It does not try every possible starting grid. That would be impossibly large. Instead, it uses a genetic algorithm: it keeps many possible starting grids, tests them, keeps the best ones, mixes and mutates them, and repeats.

## The Basic Loop

1. You draw the desired finish grid.
2. You choose `Steps`, the number of Game of Life generations to run.
3. The solver creates a population of candidate initial grids.
4. Each candidate is simulated forward for `Steps`.
5. The simulated result is compared with your target.
6. The best candidates survive.
7. New candidates are made by crossing and mutating the best ones.
8. The loop stops when it finds a perfect match or reaches the generation limit.

## How Candidates Are Scored

The score is an error number. Lower is better.

- A missing target cell is expensive.
- An extra live cell is less expensive.
- Extra cells far from the target are penalized a bit more than extra cells near it.
- If two candidates produce similarly good final grids, the solver slightly prefers the simpler initial grid with fewer live cells.

This makes the search prefer grids that actually converge toward the target instead of messy grids that only happen to contain parts of it.

## Efficiency Improvements

The current solver improves on the original simple genetic algorithm in a few ways:

- Dynamic search zone: it searches around the target, and expands that zone when `Steps` is larger.
- Guided random population: random candidates are more likely to place cells near the target shape.
- Multiple densities: the initial population includes sparse, medium, and dense candidates.
- Evaluation cache: if the same candidate appears again, the solver reuses its previous simulation result.
- Duplicate removal: repeated candidates are removed before the next generation.
- Adaptive mutation: if the solver gets stuck, mutation and random injection increase.
- Local improvement: each generation tries a few one-cell changes around the current best candidate.

## Evolution Playback

After the solver has a best initial grid, the UI can play its full evolution:

- Step `0` is the proposed initial grid.
- Step `X` is the final simulated grid.
- Blue cells are currently alive.
- Purple cells are alive and also part of the target.
- Orange cells are target cells that are still missing at that playback step.

This lets you see whether the best result really converges toward the desired finish pattern.

## Complexity

Let:

- `N` = total cells in the board, here `24 * 24 = 576`
- `P` = population size
- `G` = maximum genetic generations
- `X` = requested Game of Life steps
- `L` = local one-cell improvement tries per generation
- `C` = number of cached candidate evaluations

Simulating one candidate costs:

```text
O(X * N)
```

One genetic generation evaluates about `P` candidates plus `L` local tweaks:

```text
O((P + L) * X * N)
```

The full solver costs at most:

```text
O(G * (P + L) * X * N)
```

The cache can reduce repeated work, so the practical runtime is often better than that worst-case formula.

Memory use is roughly:

```text
O(P * N + C * N + X * N)
```

That means memory holds the current population, cached simulation results, and the optional evolution playback.

