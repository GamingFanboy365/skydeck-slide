; Skydeck Slide -- game states, physics, opponent AI, sprites
INCLUDE "hardware.inc"
INCLUDE "consts.inc"

DEF ST_TITLE EQU 0
DEF ST_INTRO EQU 1
DEF ST_PLAY  EQU 2
DEF ST_POINT EQU 3
DEF ST_OVER  EQU 4
DEF ST_CHAMP EQU 5

DEF WIN_SCORE   EQU 7
DEF PLAYER_ZMIN EQU 144
DEF PLAYER_ZMAX EQU 188
DEF PADDLE_XMAX EQU 40
DEF PUCK_XMAX   EQU 45
DEF OPP_Z       EQU 12
DEF OPP_LUNGE_Z EQU 26
DEF GOAL_NEAR   EQU 200      ; puck depth past the player
DEF GOAL_WRAP   EQU 240      ; puck went below depth 0 (past the opponent)

SECTION "Game", ROM0

; a += hl (as an index): hl = hl + a
AddAtoHL::
    add l
    ld l, a
    adc h
    sub l
    ld h, a
    ret

RunState::
    ld a, [wState]
    add a
    ld hl, StateTable
    call AddAtoHL
    ld a, [hl+]
    ld h, [hl]
    ld l, a
    jp hl

StateTable:
    dw StateTitle, StateIntro, StatePlay, StatePoint, StateOver, StateChamp

; ---------------------------------------------------------------------------
; title screen
EnterTitle::
    call LcdOff
    call LoadTitleScreen
    ld hl, TxtStart
    ld de, $9800 + 12 * 32
    ld b, TEXT_PALETTE
    call PrintDirect
    ld hl, TxtHelp1
    ld de, $9800 + 14 * 32
    ld b, TEXT_PALETTE
    call PrintDirect
    ld hl, TxtHelp2
    ld de, $9800 + 16 * 32
    ld b, TEXT_PALETTE
    call PrintDirect
    call LcdOn
    xor a
    ld [wState], a
    ld [wTimer], a
    ld hl, SongTitle
    jp PlaySong

StateTitle:
    ld hl, wTimer
    inc [hl]
    ld a, [hl]
    and $1F
    jr nz, .input
    ld a, [wTimer]
    and $20
    ld hl, TxtStart
    jr z, .show
    ld hl, TxtBlank
.show:
    ld de, $9800 + 12 * 32
    call SetRowFromString
.input:
    ldh a, [hJoyPressed]
    and (1 << PAD_START) | (1 << PAD_A)
    ret z
    call SfxBlip
    xor a
    ld [wLevel], a
    jp StartMatch

; ---------------------------------------------------------------------------
StartMatch:
    call StopMusic
    call LcdOff
    call LoadGameScreen
    call LcdOn
    ld hl, SongMatch
    ld a, [wLevel]
    cp 2
    jr nz, .song
    ld hl, SongOkta             ; the last opponent gets her own theme
.song:
    call PlaySong
    xor a
    ld [wScoreP], a
    ld [wScoreO], a
    ld [wServer], a
    ld [wPaused], a
    call ResetPositions
    ld a, ST_INTRO
    ld [wState], a
    ld a, 120
    ld [wTimer], a
    ; "VS NAME  FIRST TO 7"
    ld hl, wText
    ld a, "V"
    ld [hl+], a
    ld a, "S"
    ld [hl+], a
    ld a, " "
    ld [hl+], a
    call CopyOppName
    ld de, TxtFirstTo
.cat:
    ld a, [de]
    ld [hl+], a
    inc de
    cp $FF
    jr nz, .cat
    ld hl, wText
    ld de, $9800
    jp SetRowFromString

; copy the current opponent's 5-letter name to hl (advances hl)
CopyOppName:
    ld a, [wLevel]
    ld e, a
    add a
    add a
    add e                       ; * 5
    ld de, OppNames
    add e
    ld e, a
    adc d
    sub e
    ld d, a
    ld c, 5
.l:
    ld a, [de]
    ld [hl+], a
    inc de
    dec c
    jr nz, .l
    ret

StateIntro:
    ld hl, wTimer
    dec [hl]
    ret nz
    call UpdateHud
    ld a, ST_PLAY
    ld [wState], a
    ret

; place everything for a serve; wServer: 0 = player serves, 1 = opponent
ResetPositions:
    ld hl, wObjects
    ld bc, wObjectsEnd - wObjects
    xor a
    call Fill
    ld a, 176
    ld [wPlayerZ + 1], a
    ld a, OPP_Z
    ld [wOppZ], a
    ld a, [wServer]
    and a
    ld a, 150
    jr z, .p
    ld a, 40
.p:
    ld [wPuckZ + 1], a
    ld a, 60
    ld [wServeTimer], a
    ld a, 1
    ld [wPuckVisible], a
    ret

UpdateHud:
    ld hl, wText
    ld a, "Y"
    ld [hl+], a
    ld a, "O"
    ld [hl+], a
    ld a, "U"
    ld [hl+], a
    ld a, " "
    ld [hl+], a
    ld a, [wScoreP]
    add CHAR_ZERO
    ld [hl+], a
    ld c, 7
    ld a, " "
.sp:
    ld [hl+], a
    dec c
    jr nz, .sp
    call CopyOppName
    ld a, " "
    ld [hl+], a
    ld a, [wScoreO]
    add CHAR_ZERO
    ld [hl+], a
    ld a, $FF
    ld [hl], a
    ld hl, wText
    ld de, $9800
    jp SetRowFromString

ShowMessage:            ; hl = string
    ld de, $9800
    jp SetRowFromString

; ---------------------------------------------------------------------------
StatePlay:
    ldh a, [hJoyPressed]
    bit PAD_START, a
    jr z, .notpause
    ld a, [wPaused]
    xor 1
    ld [wPaused], a
    jr z, .unpause
    call PauseMusic
    ld hl, TxtPaused
    jp ShowMessage
.unpause:
    call ResumeMusic
    jp UpdateHud
.notpause:
    ld a, [wPaused]
    and a
    ret nz

    call UpdatePlayer
    ; opponent serve
    ld a, [wPuckLive]
    and a
    jr nz, .live
    ld a, [wServer]
    and a
    jr z, .live
    ld hl, wServeTimer
    dec [hl]
    call z, OppServe
.live:
    ld hl, wCooldown
    ld a, [hl]
    and a
    jr z, .nocd
    dec [hl]
.nocd:
    ld hl, wOppAnim
    ld a, [hl]
    and a
    jr z, .noanim
    dec [hl]
.noanim:
    ld a, [wPuckLive]
    and a
    call nz, PuckStep
    call CheckPlayerHit
    call UpdateOpp
    call CheckOppHit
    ; goals
    ld a, [wPuckLive]
    and a
    ret z
    ld a, [wPuckZ + 1]
    cp GOAL_WRAP
    jr nc, PlayerScores
    cp GOAL_NEAR
    jr nc, OppScores
    ret

PlayerScores:
    ld hl, wScoreP
    inc [hl]
    ld a, 1
    ld [wServer], a             ; the side that conceded serves
    ld hl, TxtGoal
    jr PointScored

OppScores:
    ld hl, wScoreO
    inc [hl]
    xor a
    ld [wServer], a
    ld hl, TxtMissed

PointScored:
    call ShowMessage
    call SfxGoal
    xor a
    ld [wPuckLive], a
    ld [wPuckVisible], a
    ld [wPredValid], a
    ld a, 90
    ld [wTimer], a
    ld a, ST_POINT
    ld [wState], a
    ret

StatePoint:
    ld hl, wTimer
    dec [hl]
    ret nz
    ld a, [wScoreP]
    cp WIN_SCORE
    jr z, .won
    ld a, [wScoreO]
    cp WIN_SCORE
    jr z, .lost
    call ResetPositions
    call UpdateHud
    ld a, ST_PLAY
    ld [wState], a
    ret
.won:
    ld hl, SongWin
    call PlaySong
    ld a, 1
    ld hl, TxtWin
    jr .over
.lost:
    ld hl, SongLose
    call PlaySong
    xor a
    ld hl, TxtLose
.over:
    ld [wWon], a
    call ShowMessage
    ld a, ST_OVER
    ld [wState], a
    ld a, 40
    ld [wTimer], a
    ret

StateOver:
    ld hl, wTimer
    ld a, [hl]
    and a
    jr z, .wait
    dec [hl]
    ret
.wait:
    ldh a, [hJoyPressed]
    and (1 << PAD_START) | (1 << PAD_A)
    ret z
    ld a, [wWon]
    and a
    jp z, EnterTitle
    ld hl, wLevel
    inc [hl]
    ld a, [hl]
    cp 3
    jp nz, StartMatch
    ld hl, SongWin
    call PlaySong
    ld hl, TxtChamp
    call ShowMessage
    ld a, ST_CHAMP
    ld [wState], a
    ret

StateChamp:
    ldh a, [hJoyPressed]
    and (1 << PAD_START) | (1 << PAD_A)
    ret z
    jp EnterTitle

; ---------------------------------------------------------------------------
; player paddle: the d-pad accelerates; letting go stops that axis
DEF PAD_ACCEL EQU $0030
DEF PAD_VMAX  EQU $0180

UpdatePlayer:
    ldh a, [hJoyHeld]
    ld b, a
    ld de, -PAD_ACCEL
    bit PAD_UP, b
    jr nz, .zacc
    ld de, PAD_ACCEL
    bit PAD_DOWN, b
    jr nz, .zacc
    xor a
    ld [wPlayerVZ], a
    ld [wPlayerVZ + 1], a
    jr .xaxis
.zacc:
    ld hl, wPlayerVZ
    call AddWordAtHL
.xaxis:
    ld de, -PAD_ACCEL
    bit PAD_LEFT, b
    jr nz, .xacc
    ld de, PAD_ACCEL
    bit PAD_RIGHT, b
    jr nz, .xacc
    xor a
    ld [wPlayerVX], a
    ld [wPlayerVX + 1], a
    jr .caps
.xacc:
    ld hl, wPlayerVX
    call AddWordAtHL
.caps:
    ld hl, wPlayerVZ
    ld bc, PAD_VMAX
    call Cap16
    ld hl, wPlayerVX
    ld bc, PAD_VMAX
    call Cap16
    ; move
    ld hl, wPlayerVZ
    call LoadDE
    ld hl, wPlayerZ
    call AddWordAtHL
    ld hl, wPlayerVX
    call LoadDE
    ld hl, wPlayerX
    call AddWordAtHL
    ; keep the paddle in the near part of the table
    ld a, [wPlayerZ + 1]
    cp PLAYER_ZMIN
    jr nc, .z1
    ld a, PLAYER_ZMIN
    jr .zclamp
.z1:
    cp PLAYER_ZMAX
    jr c, .zok
    ld a, PLAYER_ZMAX
.zclamp:
    ld [wPlayerZ + 1], a
    xor a
    ld [wPlayerZ], a
    ld [wPlayerVZ], a
    ld [wPlayerVZ + 1], a
.zok:
    ld hl, wPlayerX
    ld b, PADDLE_XMAX
    call ClampX
    ret nc
    xor a
    ld [wPlayerVX], a
    ld [wPlayerVX + 1], a
    ret

; de = 16-bit word at hl
LoadDE:
    ld a, [hl+]
    ld e, a
    ld d, [hl]
    ret

; clamp the signed 8.8 word at hl to +/- b; carry set if it was clamped
ClampX:
    inc hl
    ld a, [hl]
    bit 7, a
    jr nz, .neg
    cp b
    jr c, .ok
    ld a, b
    jr .set
.neg:
    ld c, a
    ld a, b
    cpl
    inc a                       ; a = -b
    cp c                        ; carry if -b > value
    jr z, .ok
    jr c, .ok
.set:
    ld [hl-], a
    xor a
    ld [hl], a
    scf
    ret
.ok:
    dec hl
    and a
    ret

; limit the signed word at hl to +/- bc
Cap16:
    ld a, [hl+]
    ld e, a
    ld a, [hl-]
    ld d, a
    bit 7, d
    jr nz, .neg
    ld a, c
    sub e
    ld a, b
    sbc d
    ret nc
    ld a, c
    ld [hl+], a
    ld [hl], b
    dec hl
    ret
.neg:
    call NegDE
    ld a, c
    sub e
    ld a, b
    sbc d
    ret nc
    ld d, b
    ld e, c
    call NegDE
    ld a, e
    ld [hl+], a
    ld [hl], d
    dec hl
    ret

; slow the word at hl by one step, but only while faster than 1.25 per frame
Friction16:
    ld a, [hl+]
    ld e, a
    ld d, [hl]
    dec hl
    bit 7, d
    jr z, .pos
    push de
    call NegDE
    call .fast
    pop de
    ret nc
    inc de
    jr .store
.pos:
    call .fast
    ret nc
    dec de
.store:
    ld a, e
    ld [hl+], a
    ld [hl], d
    dec hl
    ret
.fast:                          ; carry set if de >= $0140
    ld a, e
    sub $40
    ld a, d
    sbc $01
    ccf
    ret

; ---------------------------------------------------------------------------
; puck physics, one frame. Also used by Predict with sound muted.
DEF PUCK_VZMAX EQU $0300
DEF PUCK_VXMAX EQU $0200

PuckStep:
    ld hl, wPuckVX
    call Friction16
    ld hl, wPuckVZ
    call Friction16
    call EnforceMinVZ
    ld hl, wPuckVZ
    ld bc, PUCK_VZMAX
    call Cap16
    ld hl, wPuckVX
    ld bc, PUCK_VXMAX
    call Cap16
    ld hl, wPuckVX
    call LoadDE
    ld hl, wPuckX
    call AddWordAtHL
    ld hl, wPuckX
    ld b, PUCK_XMAX
    call ClampX
    jr nc, .nowall
    ld hl, wPuckVX
    call LoadDE
    call NegDE
    ld a, e
    ld [wPuckVX], a
    ld a, d
    ld [wPuckVX + 1], a
    call SfxWall
.nowall:
    ld hl, wPuckVZ
    call LoadDE
    ld hl, wPuckZ
    jp AddWordAtHL

; a live puck never crawls: depth speed is at least 0.5 per frame
EnforceMinVZ:
    ld a, [wPuckVZ + 1]
    bit 7, a
    jr nz, .neg
    and a
    ret nz
    ld a, [wPuckVZ]
    cp $80
    ret nc
    and a
    jr z, .setneg
    ld a, $80
    ld [wPuckVZ], a
    ret
.neg:
    cp $FF
    ret nz
    ld a, [wPuckVZ]
    cp $81
    ret c
.setneg:
    ld a, $80
    ld [wPuckVZ], a
    ld a, $FF
    ld [wPuckVZ + 1], a
    ret

; ---------------------------------------------------------------------------
; the player's paddle meets the puck
CheckPlayerHit:
    ld a, [wCooldown]
    and a
    ret nz
    ld a, [wPlayerZ + 1]
    ld b, a
    ld a, [wPuckZ + 1]
    sub b
    add 6                       ; puck depth within [paddle-6, paddle+2]
    cp 9
    ret nc
    ld a, [wPlayerX + 1]
    ld b, a
    ld a, [wPuckX + 1]
    sub b
    ld c, a                     ; c = puck x - paddle x
    add 11
    cp 23
    ret nc
    ; new depth speed: -(|vz| + 0.25) + paddle depth speed, at least 0.5 away
    ld hl, wPuckVZ
    call LoadDE
    bit 7, d
    call nz, NegDE
    ld hl, $0040
    add hl, de
    ld d, h
    ld e, l
    call NegDE
    ld a, [wPlayerVZ]
    add e
    ld e, a
    ld a, [wPlayerVZ + 1]
    adc d
    ld d, a
    bit 7, d
    jr z, .force
    ld a, d
    cp $FF
    jr nz, .vzok
.force:
    ld de, $FF00
.vzok:
    ld a, e
    ld [wPuckVZ], a
    ld a, d
    ld [wPuckVZ + 1], a
    ; sideways: vx + paddle vx + offset * 8
    ld a, c
    ld l, a
    add a
    sbc a
    ld h, a
    add hl, hl
    add hl, hl
    add hl, hl
    ld a, [wPuckVX]
    ld e, a
    ld a, [wPuckVX + 1]
    ld d, a
    add hl, de
    ld a, [wPlayerVX]
    ld e, a
    ld a, [wPlayerVX + 1]
    ld d, a
    add hl, de
    ld a, l
    ld [wPuckVX], a
    ld a, h
    ld [wPuckVX + 1], a
    ; place the puck just in front of the paddle
    ld a, [wPlayerZ + 1]
    sub 7
    ld [wPuckZ + 1], a
    ld a, 10
    ld [wCooldown], a
    ld a, 1
    ld [wPuckLive], a
    call SfxHit
    jp Predict

; ---------------------------------------------------------------------------
; Run the puck forward (silently) until it reaches the opponent's line, note
; where it gets to, then put it back. The opponent aims for that spot, with
; an error that shrinks as the level goes up.
Predict:
    ld hl, wPuckX
    ld de, wPuckSave
    ld bc, 8
    call Copy
    ld a, 1
    ld [wSilent], a
    ld b, 0
.loop:
    push bc
    call PuckStep
    pop bc
    ld a, [wPuckZ + 1]
    cp GOAL_WRAP
    jr nc, .done
    cp OPP_Z + 2
    jr c, .done
    inc b
    jr nz, .loop
.done:
    ld a, [wPuckX + 1]
    ld [wPredX], a
    ld hl, wPuckSave
    ld de, wPuckX
    ld bc, 8
    call Copy
    xor a
    ld [wSilent], a
    call Random
    ld c, a
    ld a, [wLevel]
    add 4
    ld b, a
    ld a, c
.shift:
    sra a
    dec b
    jr nz, .shift
    ld b, a
    ld a, [wPredX]
    add b
    ld [wPredX], a
    ld a, 1
    ld [wPredValid], a
    ret

; ---------------------------------------------------------------------------
UpdateOpp:
    ld a, [wPredValid]
    and a
    jr z, .lazy
    ld a, [wPredX]
    jr .have
.lazy:
    ld a, [wPuckX + 1]          ; drift halfway toward the puck's line
    sra a
.have:
    ld b, a
    ld a, [wOppX + 1]
    ld c, a
    ld a, b
    sub c
    ld b, a                     ; b = target - x
    bit 7, a
    jr z, .abs
    cpl
    inc a
.abs:
    cp 2
    jr nc, .move
    xor a
    ld [wOppVX], a
    ld [wOppVX + 1], a
    jr .integrate
.move:
    ld a, [wLevel]
    add a
    ld hl, OppSpeed
    call AddAtoHL
    call LoadDE
    bit 7, b
    call nz, NegDE
    ld a, e
    ld [wOppVX], a
    ld a, d
    ld [wOppVX + 1], a
.integrate:
    ld hl, wOppVX
    call LoadDE
    ld hl, wOppX
    call AddWordAtHL
    ld hl, wOppX
    ld b, PADDLE_XMAX
    call ClampX
    ; level 3 opponent steps forward to meet a close puck
    ld c, OPP_Z
    ld a, [wLevel]
    cp 2
    jr nz, .zmove
    ld a, [wPredValid]
    and a
    jr z, .zmove
    ld a, [wPuckZ + 1]
    cp 60
    jr nc, .zmove
    ld c, OPP_LUNGE_Z
.zmove:
    ld a, [wOppZ]
    cp c
    ret z
    jr c, .zinc
    dec a
    ld [wOppZ], a
    ret
.zinc:
    inc a
    ld [wOppZ], a
    ret

OppSpeed:
    dw $0090, $00E0, $0140
OppReturnMax:
    dw $0180, $0220, $0300

CheckOppHit:
    ld a, [wPuckLive]
    and a
    ret z
    ld a, [wPuckVZ + 1]
    bit 7, a
    ret z
    ld a, [wOppZ]
    ld b, a
    ld a, [wPuckZ + 1]
    sub b
    add 4
    cp 10
    ret nc
    ld a, [wOppX + 1]
    ld b, a
    ld a, [wPuckX + 1]
    sub b
    add 11
    cp 23
    ret nc
    ; send it back faster at higher levels and as the rally goes on
    ld hl, wRally
    ld a, [hl]
    cp 15
    jr nc, .rallymax
    inc [hl]
.rallymax:
    ld hl, wPuckVZ
    call LoadDE
    call NegDE
    ld a, [wRally]
    add a
    add a
    add a                       ; rally * 8
    ld b, a
    ld a, [wLevel]
    swap a
    add $20
    add b
    ld l, a
    ld h, 0
    add hl, de
    ld a, l
    ld [wPuckVZ], a
    ld a, h
    ld [wPuckVZ + 1], a
    ; each level has its own top return speed
    ld a, [wLevel]
    add a
    ld hl, OppReturnMax
    call AddAtoHL
    ld a, [hl+]
    ld c, a
    ld b, [hl]
    ld hl, wPuckVZ
    call Cap16
    call OppAim
    ld a, [wOppZ]
    add 6
    ld [wPuckZ + 1], a
    xor a
    ld [wPredValid], a
    ld a, 16
    ld [wOppAnim], a
    jp SfxOppHit

; random sideways speed, wider at higher levels and in long rallies
OppAim:
    call Random
    ld e, a
    add a
    sbc a
    ld d, a
    ld a, [wRally]
    srl a
    srl a
    ld b, a
    ld a, [wLevel]
    add b
    cp 3
    jr c, .shifts
    ld a, 2
.shifts:
    and a
    jr z, .set
    ld b, a
.sh:
    sla e
    rl d
    dec b
    jr nz, .sh
.set:
    ld a, e
    ld [wPuckVX], a
    ld a, d
    ld [wPuckVX + 1], a
    ret

OppServe:
    ld a, [wLevel]
    swap a
    add a
    add $20
    ld [wPuckVZ], a
    ld a, 1
    ld [wPuckVZ + 1], a
    call OppAim
    ld a, 1
    ld [wPuckLive], a
    ld a, 16
    ld [wOppAnim], a
    jp SfxOppHit

; ---------------------------------------------------------------------------
; sprites
DrawSprites::
    ld hl, wShadowOAM
    ld a, [wState]
    cp ST_TITLE
    jr z, .clear
    ld a, [wPuckVisible]
    and a
    call nz, DrawPuck
    ; player paddle
    ld a, [wPlayerZ + 1]
    ld b, a
    ld a, [wPlayerX + 1]
    ld c, a
    xor a
    ld [wDrawAttr], a
    call DrawPaddle
    ; opponent paddle and character
    ld a, [wOppZ]
    ld b, a
    ld a, [wOppX + 1]
    ld c, a
    ld a, 1
    ld [wDrawAttr], a
    call DrawPaddle
    call DrawChar
.clear:
    ld a, l
    cp 160
    ret nc
    xor a
    ld [hl+], a
    inc l
    inc l
    inc l
    jr .clear

; b = depth, c = signed x  ->  d = screen y, e = screen x (hl preserved)
Project:
    push hl
    ld hl, PerspScale
    ld a, b
    call AddAtoHL
    ld e, [hl]
    ld a, c
    bit 7, a
    jr z, .pos
    cpl
    inc a
    call Mul8
    add hl, hl
    add hl, hl
    ld a, CENTER_X
    sub h
    jr .gotx
.pos:
    call Mul8
    add hl, hl
    add hl, hl
    ld a, h
    add CENTER_X
.gotx:
    ld e, a
    ld hl, PerspY
    ld a, b
    call AddAtoHL
    ld d, [hl]
    pop hl
    ret

DrawPuck:
    ld a, [wPuckZ + 1]
    ld b, a
    ld a, [wPuckX + 1]
    ld c, a
    call Project
    push hl
    ld hl, PuckSizeByZ
    ld a, b
    srl a
    srl a
    call AddAtoHL
    ld a, [hl]
    ld hl, PuckSprites
    call AddAtoHL
    ld c, [hl]
    pop hl
    ld a, d
    add 12
    ld [hl+], a
    ld a, e
    add 4
    ld [hl+], a
    ld a, c
    ld [hl+], a
    ld a, 2
    ld [hl+], a
    ret

; b = depth, c = x, wDrawAttr = palette; hl = OAM pointer (advanced)
DrawPaddle:
    call Project
    push hl
    ld hl, PaddleSizeByZ
    ld a, b
    srl a
    srl a
    call AddAtoHL
    ld a, [hl]
    ld c, a
    add a
    add a
    add c                       ; * 5 bytes per entry
    ld hl, PaddleSprites
    call AddAtoHL
    ld a, [hl+]
    ld [wDrawCount], a
    ld a, [hl+]
    add e
    add 8
    ld [wDrawX], a
    ld a, d
    add 14
    ld [wDrawY], a
    ld a, l
    ld [wDrawPtr], a
    ld a, h
    ld [wDrawPtr + 1], a
    pop hl
.loop:
    ld a, [wDrawY]
    ld [hl+], a
    ld a, [wDrawX]
    ld [hl+], a
    add 8
    ld [wDrawX], a
    push hl
    ld a, [wDrawPtr]
    ld l, a
    ld a, [wDrawPtr + 1]
    ld h, a
    ld c, [hl]
    inc hl
    ld a, l
    ld [wDrawPtr], a
    ld a, h
    ld [wDrawPtr + 1], a
    pop hl
    ld a, c
    ld [hl+], a
    ld a, [wDrawAttr]
    ld [hl+], a
    ld a, [wDrawCount]
    dec a
    ld [wDrawCount], a
    jr nz, .loop
    ret

; the opponent stands behind its paddle: 24x32 from six 8x16 sprites (VRAM bank 1)
DrawChar:
    ld a, [wOppZ]
    ld b, a
    ld a, [wOppX + 1]
    ld c, a
    call Project
    push hl
    ld a, [wLevel]
    add a
    ld c, a
    ld a, [wOppAnim]
    and a
    jr z, .idle
    inc c
.idle:
    ld a, c
    add a
    add c
    add a                       ; 6 tiles per frame
    ld hl, CharSprites
    call AddAtoHL
    ld a, l
    ld [wDrawPtr], a
    ld a, h
    ld [wDrawPtr + 1], a
    ld a, [wLevel]
    add 3 | $08                 ; palette 3+level, tiles from VRAM bank 1
    ld [wDrawAttr], a
    pop hl
    ld a, d
    sub 14
    ld [wDrawY], a              ; top row OAM y
    ld a, e
    sub 4
    ld [wDrawX], a              ; left column OAM x
    ld b, 0                     ; piece 0..5, three per row
.piece:
    ld a, b
    cp 3
    ld a, [wDrawY]
    jr c, .row0
    add 16
.row0:
    ld [hl+], a
    ld a, b
    cp 3
    jr c, .col
    sub 3
.col:
    add a
    add a
    add a                       ; column * 8
    ld c, a
    ld a, [wDrawX]
    add c
    ld [hl+], a
    push hl
    ld a, [wDrawPtr]
    ld l, a
    ld a, [wDrawPtr + 1]
    ld h, a
    ld a, b
    call AddAtoHL
    ld c, [hl]
    pop hl
    ld a, c
    ld [hl+], a
    ld a, [wDrawAttr]
    ld [hl+], a
    inc b
    ld a, b
    cp 6
    jr nz, .piece
    ret

; ---------------------------------------------------------------------------
SECTION "Text", ROM0
TxtStart:   db "    PRESS START     ", $FF
TxtBlank:   db "                    ", $FF
TxtHelp1:   db " D-PAD MOVES PADDLE ", $FF
TxtHelp2:   db "  FIRST TO 7 WINS   ", $FF
TxtFirstTo: db "  FIRST TO 7", $FF
TxtPaused:  db "      PAUSED", $FF
TxtGoal:    db "   GOAL! YOU SCORE", $FF
TxtMissed:  db "     MISSED!", $FF
TxtWin:     db " YOU WIN!  PRESS A", $FF
TxtLose:    db " YOU LOSE. PRESS A", $FF
TxtChamp:   db " CHAMPION! PRESS A", $FF
OppNames:   db "TOMO RUSTYOKTA "

; ---------------------------------------------------------------------------
SECTION "Game variables", WRAM0
wState::     ds 1
wTimer::     ds 1
wLevel::     ds 1
wScoreP::    ds 1
wScoreO::    ds 1
wServer::    ds 1
wPaused::    ds 1
wWon::       ds 1
wText::      ds 24
wDrawAttr::  ds 1
wDrawCount:: ds 1
wDrawX::     ds 1
wDrawY::     ds 1
wDrawPtr::   ds 2
wPuckSave::  ds 8
wPredX::     ds 1
; everything below is cleared by ResetPositions
wObjects::
wPuckX::     ds 2           ; signed 8.8, 0 = centre
wPuckZ::     ds 2           ; 8.8, 0 = opponent's end, 192 = player's end
wPuckVX::    ds 2
wPuckVZ::    ds 2
wPlayerX::   ds 2
wPlayerZ::   ds 2
wPlayerVX::  ds 2
wPlayerVZ::  ds 2
wOppX::      ds 2
wOppVX::     ds 2
wOppZ::      ds 1
wPredValid:: ds 1
wPuckLive::  ds 1
wPuckVisible:: ds 1
wCooldown::  ds 1
wServeTimer:: ds 1
wOppAnim::   ds 1
wRally::     ds 1
wObjectsEnd::
