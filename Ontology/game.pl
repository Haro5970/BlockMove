:- encoding(utf8).
% ==========================================
% Block Move 게임 온톨로지
% ==========================================

% --- 동적 서술어 (Dynamic Predicates) ---
% 게임 도중 상태가 변하는 요소들입니다.
:- dynamic player/2.    % player(X, Y)
:- dynamic block/2.     % block(X, Y)
:- dynamic wall/2.      % wall(X, Y)
:- dynamic hole/2.      % hole(X, Y)

% --- 정적 사실 (Static Facts) ---
% 보드 크기: board_size(Width, Height)
board_size(20, 15).

% 초기 벽/구멍 위치 (테스트용, 실제 게임에서는 sync_state로 덮어씌워짐)
wall(2, 2).
wall(3, 2).
wall(4, 2).

hole(5, 5).

% --- 초기 상태 (Initial State) ---
player(1, 1).
block(3, 3).
block(2, 4).

% --- 규칙 (Rules) ---

% 방향 정의: direction(Name, DX, DY)
direction(up, 0, -1).
direction(down, 0, 1).
direction(left, -1, 0).
direction(right, 1, 0).

% Case 1: 빈 공간으로 이동
can_move(PX, PY, NX, NY, DX, DY) :-
    (var(NX) -> NX is PX + DX ; true),
    (var(NY) -> NY is PY + DY ; true),
    in_bounds(NX, NY),      % 보드 내부인지 확인
    \+ wall(NX, NY),        % 벽이 없어야 함
    \+ block(NX, NY),       % 블록이 없어야 함
    retract(player(_, _)),  % 현재 플레이어 위치 삭제
    assert(player(NX, NY)), % 새로운 위치 추가
    format('Player moved to (~w, ~w)~n', [NX, NY]).

% Case 2: 블록 밀기
can_move(PX, PY, NX, NY, DX, DY) :-
    (var(NX) -> NX is PX + DX ; true),
    (var(NY) -> NY is PY + DY ; true),
    block(NX, NY),          % 이동하려는 곳에 블록이 있음
    NNX is NX + DX,         % 블록이 밀릴 다음 위치
    NNY is NY + DY,
    in_bounds(NNX, NNY),    % 블록 다음 위치가 보드 내부여야 함
    \+ wall(NNX, NNY),      % 블록 뒤에 벽이 없어야 함
    \+ block(NNX, NNY),     % 블록 뒤에 다른 블록이 없어야 함
    
    % 블록 이동
    retract(block(NX, NY)),
    assert(block(NNX, NNY)),
    
    % 플레이어 이동
    retract(player(_, _)),
    assert(player(NX, NY)),
    
    format('Player pushed block to (~w, ~w)~n', [NNX, NNY]),
    
    % 구멍 확인
    check_hole(NNX, NNY).

% Case 3: 이동 불가
can_move(_, _, _, _, _, _) :-
    write('Cannot move there.'), nl, fail.

% --- 상태 변경 없는 확인용 (Check Only) ---
is_valid_move(PX, PY, DX, DY) :-
    NX is PX + DX,
    NY is PY + DY,
    in_bounds(NX, NY),
    \+ wall(NX, NY),
    (block(NX, NY) ->
        NNX is NX + DX, NNY is NY + DY,
        in_bounds(NNX, NNY),
        \+ wall(NNX, NNY),
        \+ block(NNX, NNY)
    ; true).

% --- 보조 규칙 (Helpers) ---

% 보드 범위 확인
in_bounds(X, Y) :-
    board_size(W, H),
    X > 0, X =< W,
    Y > 0, Y =< H.

% 구멍에 블록이 빠졌는지 확인
check_hole(X, Y) :-
    hole(X, Y),
    retract(block(X, Y)),   % 블록 제거
    format('Block fell into hole at (~w, ~w)!~n', [X, Y]),
    check_win.              % 승리 조건 확인
check_hole(_, _).           % 구멍이 아니면 아무 일도 없음

% 승리 조건 확인
check_win :-
    \+ block(_, _),
    write('*** All blocks are in holes! YOU WIN! ***'), nl.
check_win.
