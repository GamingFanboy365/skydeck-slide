; Skydeck Slide -- game states, physics, opponent AI, sprites
INCLUDE "hardware.inc"
INCLUDE "consts.inc"

DEF ST_TITLE EQU 0
DEF ST_INTRO EQU 1
DEF ST_PLAY  EQU 2
DEF ST_POINT EQU 3
DEF ST_OVER  EQU 4
DEF ST_CHAMP EQU 5
DEF ST_CARD  EQU 6
DEF ST_GLOSS EQU 7
DEF ST_HOWTO EQU 8

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
    dw StateTitle, StateIntro, StatePlay, StatePoint, StateOver, StateChamp, StateCard
    dw StateGloss, StateHowto

; ---------------------------------------------------------------------------
; title screen
EnterTitle::
    call DrawTitle
    ld hl, SongTitle
    jp PlaySong

; back from the glossary: same screen, the title music keeps playing
BackToTitle:
    push af
    call DrawTitle
    pop af
    ld [wMenu], a
    ret

DrawTitle:
    call LcdOff
    call LoadTitleScreen
    ld hl, TxtMenuStart
    ld de, $9800 + 12 * 32
    ld b, TEXT_PALETTE
    call PrintDirect
    ld hl, TxtMenuHowto
    ld de, $9800 + 14 * 32
    ld b, TEXT_PALETTE
    call PrintDirect
    ld hl, TxtMenuGloss
    ld de, $9800 + 16 * 32
    ld b, TEXT_PALETTE
    call PrintDirect
    call LcdOn
    xor a
    ld [wState], a
    ld [wTimer], a
    ld [wMenu], a
    ret

StateTitle:
    ld hl, wTimer
    inc [hl]
    ldh a, [hJoyPressed]
    ld b, a
    bit PAD_DOWN, b
    jr z, .up
    ld a, [wMenu]
    inc a
    cp 3
    jr c, .set
    xor a
    jr .set
.up:
    bit PAD_UP, b
    jr z, .pick
    ld a, [wMenu]
    and a
    jr nz, .dec
    ld a, 3
.dec:
    dec a
.set:
    ld [wMenu], a
    call SfxBlip
.pick:
    ldh a, [hJoyPressed]
    and (1 << PAD_START) | (1 << PAD_A)
    ret z
    call SfxBlip
    ld a, [wMenu]
    dec a
    jr z, EnterHowto
    dec a
    jr z, EnterGlossary
    xor a
    ld [wLevel], a
    jp EnterCard

; ---------------------------------------------------------------------------
; how to play: the city table with arrows, a paddle and a puck, text on top
EnterHowto:
    call LcdOff
    ld a, HOWTO_SCREEN
    call LoadScreen
    ld hl, TxtHowto
    ld de, $9800
    ld b, 0
.lines:
    push de
    call PrintDirect
    pop de
    ld a, e
    add 32
    ld e, a
    jr nc, .nc
    inc d
.nc:
    ld a, [hl]
    cp $FE
    jr nz, .lines
    call LcdOn
    ld hl, wObjects
    ld bc, wObjectsEnd - wObjects
    xor a
    call Fill
    ld a, 176
    ld [wPlayerZ + 1], a
    ld a, -10
    ld [wPlayerX + 1], a
    ld a, 150
    ld [wPuckZ + 1], a
    ld a, 8
    ld [wPuckX + 1], a
    ld a, ST_HOWTO
    ld [wState], a
    ret

StateHowto:
    ldh a, [hJoyPressed]
    and (1 << PAD_B) | (1 << PAD_A) | (1 << PAD_START)
    ret z
    call SfxBlip
    ld a, 1
    jp BackToTitle

; ---------------------------------------------------------------------------
; glossary: pages of text, some with an opponent standing in the middle
EnterGlossary:
    xor a
    ld [wPage], a
    ld a, ST_GLOSS
    ld [wState], a
    jp DrawPage

StateGloss:
    ldh a, [hJoyPressed]
    ld b, a
    and (1 << PAD_B) | (1 << PAD_START)
    ld a, 2
    jp nz, BackToTitle
    bit PAD_RIGHT, b
    jr nz, .next
    bit PAD_LEFT, b
    ret z
    ld a, [wPage]
    and a
    jr nz, .dec
    ld a, NUM_PAGES
.dec:
    dec a
    jr .turn
.next:
    ld a, [wPage]
    inc a
    cp NUM_PAGES
    jr c, .turn
    xor a
.turn:
    ld [wPage], a
    call SfxBlip
    ; fall through

DrawPage:
    call LcdOff
    ld a, BANK(GlossaryPages)
    ld [$2000], a
    ld a, [wPage]
    add a
    ld hl, GlossaryPages
    call AddAtoHL
    ld a, [hl+]
    ld h, [hl]
    ld l, a
    ld a, [hl+]
    ld [wGlossStage], a
    ld a, [hl+]
    ld [wGlossWho], a
    ld a, l
    ld [wGlossPtr], a
    ld a, h
    ld [wGlossPtr + 1], a
    ld a, [wGlossStage]
    call LoadVignette           ; switches ROM banks: fetch the text again after
    ld a, BANK(GlossaryPages)
    ld [$2000], a
    ld a, [wGlossPtr]
    ld l, a
    ld a, [wGlossPtr + 1]
    ld h, a
    ld de, $9800 + 32 * 8
    ld b, 0                     ; title
    call PrintDirect
    ld de, $9800 + 32 * 16
    ld b, 0                     ; footer
    call PrintDirect
    ld de, $9800 + 32 * 10
.body:
    ld a, [hl]
    cp $FE
    jr z, .done
    ld b, 0
    push de
    call PrintDirect
    pop de
    ld a, e
    add 32
    ld e, a
    jr nc, .body
    inc d
    jr .body
.done:
    ld a, [wGlossWho]
    cp $FF
    jr z, .on
    call LoadOpponentGfx
.on:
    jp LcdOn

; ---------------------------------------------------------------------------
; ---------------------------------------------------------------------------
; splash card before each match: stage number, place, opponent
EnterCard:
    call StopMusic
    call LcdOff
    ld a, [wLevel]
    call LoadVignette
    ; the level's six lines: 21 bytes each, 126 per level
    ld hl, CardLines
    ld a, [wLevel]
    and a
    jr z, .lines
    ld b, a
    ld de, 126
.skip:
    add hl, de
    dec b
    jr nz, .skip
.lines:
    ld de, $9800 + 32 * 8
    ld b, 0                     ; stage number
    call PrintDirect
    ld de, $9800 + 32 * 9
    ld b, 0                     ; the place
    call PrintDirect
    ld de, $9800 + 32 * 11
    ld b, 0                     ; VS name
    call PrintDirect
    ld de, $9800 + 32 * 13
    ld b, 0                     ; the opponent's opening line
    call PrintDirect
    ld de, $9800 + 32 * 14
    ld b, 0
    call PrintDirect
    ld de, $9800 + 32 * 15
    ld b, 0
    call PrintDirect
    ld a, [wLevel]
    call LoadOpponentGfx
    call LcdOn
    ld hl, SongMatch
    ld a, [wLevel]
    cp 4
    jr nz, .song
    ld hl, SongOkta             ; Okta has her own theme
.song:
    call PlaySong
    ld a, ST_CARD
    ld [wState], a
    ld a, 150
    ld [wTimer], a
    ret

; a = stage: its palettes, tiles and full map, then rows 7-17 become a text
; panel (palette 0) with bands on rows 7 and 17. The opponent stands at the
; top exactly as in a match. LCD off.
LoadVignette:
    call LoadScreen
    ld a, 1
    ldh [rVBK], a
    ld hl, CardTiles
    ld de, $9000 + 127 * 16     ; slot 383: last BG tile of VRAM bank 1
    ld bc, CardTilesEnd - CardTiles
    call Copy
    xor a
    ldh [rVBK], a
    ld hl, $9800 + 32 * 7
    ld bc, 32 * 11
    ld a, CHAR_SPACE
    call Fill
    ld a, 1
    ldh [rVBK], a
    ld hl, $9800 + 32 * 7
    ld bc, 32 * 11
    xor a
    call Fill
    xor a
    ldh [rVBK], a
    ld hl, $9800 + 32 * 7
    call BandRow
    ld hl, $9800 + 32 * 17
    call BandRow
    ; the opponent stands at the centre of the far end
    xor a
    ld [wOppX], a
    ld [wOppX + 1], a
    ld [wOppAnim], a
    ld a, OPP_Z
    ld [wOppZ], a
    ret

; dark card background, gold bands on rows 1 and 17 (LCD off)
ClearCardScreen:
    ld hl, CardPalettes
    call LoadBgPalettes
    xor a
    ldh [rVBK], a
    ld hl, CardTiles
    ld de, $9000 + 64 * 16
    ld bc, CardTilesEnd - CardTiles
    call Copy
    ld hl, $9800
    ld bc, 32 * 18
    ld a, CHAR_SPACE
    call Fill
    ld a, 1
    ldh [rVBK], a
    ld hl, $9800
    ld bc, 32 * 18
    xor a
    call Fill
    xor a
    ldh [rVBK], a
    ld hl, $9800 + 32 * 1
    call BandRow
    ld hl, $9800 + 32 * 17
    jp BandRow

; a = opponent: their two sprite palettes (3 and 4) and 64 tiles (LCD off)
LoadOpponentGfx:
    push af
    swap a                      ; 16 bytes per opponent
    ld hl, CharPalettes
    call AddAtoHL
    ld a, $80 | (3 * 8)
    ldh [rOCPS], a
    ld c, 16
.pal:
    ld a, [hl+]
    ldh [rOCPD], a
    dec c
    jr nz, .pal
    pop af
    ld c, a
    add a
    add c                       ; 3 bytes per entry
    ld hl, OppTileTable
    call AddAtoHL
    ld a, [hl+]
    ld [$2000], a               ; the opponent's ROM bank
    ld a, [hl+]
    ld h, [hl]
    ld l, a
    ld a, 1
    ldh [rVBK], a
    ld de, $8000
    ld bc, 64 * 16
    call Copy
    xor a
    ldh [rVBK], a
    ret

; a row of the gold band tile (slot 64, palette 1) at hl
BandRow:
    push hl
    ld c, 20
.t:
    ld a, 127
    ld [hl+], a
    dec c
    jr nz, .t
    pop hl
    ld a, 1
    ldh [rVBK], a
    ld c, 20
.a:
    ld a, $08                   ; palette 0, tile from VRAM bank 1
    ld [hl+], a
    dec c
    jr nz, .a
    xor a
    ldh [rVBK], a
    ret

StateCard:
    ld hl, wTimer
    ld a, [hl]
    and a
    jr z, StartMatch
    dec [hl]
    cp 120                      ; can be skipped after half a second
    ret nc
    ldh a, [hJoyPressed]
    and (1 << PAD_START) | (1 << PAD_A)
    ret z
    ; fall through

StartMatch:
    call LcdOff
    call LoadGameScreen
    call LcdOn
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
    cp NUM_LEVELS
    jp nz, EnterCard
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
    ld hl, OppErrShift
    call LevelByte
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
    ; from the fifth opponent on, step forward to meet a close puck
    ld c, OPP_Z
    ld a, [wLevel]
    cp 4
    jr c, .zmove
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

; difficulty, one entry per opponent (Tomo .. Nova)
OppSpeed:       ; sideways speed while heading for the predicted spot
    dw $0080, $0098, $00B8, $00D8, $0100, $0128, $0150
OppReturnMax:   ; fastest return
    dw $0160, $0190, $01C0, $0200, $0240, $0280, $02C0
OppServeSpeed:
    dw $0110, $0120, $0130, $0140, $0150, $0160, $0170
OppErrShift:    ; aiming error = random >> this (bigger = more accurate)
    db 3, 3, 4, 4, 5, 5, 6
OppReturnBonus: ; extra depth speed on each return
    db $20, $24, $28, $30, $38, $40, $48
OppAimShift:    ; how wide the return angles are
    db 0, 0, 1, 1, 1, 2, 2

; a = table entry for the current level from the byte table at hl
LevelByte:
    ld a, [wLevel]
    call AddAtoHL
    ld a, [hl]
    ret

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
    push de
    ld hl, OppReturnBonus
    call LevelByte
    pop de
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
    push de
    ld hl, OppAimShift
    call LevelByte
    pop de
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
    add a
    ld hl, OppServeSpeed
    call AddAtoHL
    ld a, [hl+]
    ld [wPuckVZ], a
    ld a, [hl]
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
    jr nz, .notitle
    ld a, [wMenu]               ; a puck points at the chosen menu line
    add a
    add a
    add a
    add a                       ; 16 pixels between the lines
    add 12 * 8 + 16
    ld [hl+], a
    ld a, 36 + 8
    ld [hl+], a
    ld a, [PuckSprites + 4]
    ld [hl+], a
    ld a, 2
    ld [hl+], a
    jr .clear
.notitle:
    cp ST_HOWTO
    jr nz, .nothowto
    ld a, 1
    ld [wPuckVisible], a
    call DrawPuck
    ld a, [wPlayerZ + 1]
    ld b, a
    ld a, [wPlayerX + 1]
    ld c, a
    xor a
    ld [wDrawAttr], a
    call DrawPaddle
    jr .clear
.nothowto:
    cp ST_GLOSS
    jr nz, .notgloss
    ld a, [wGlossWho]
    cp $FF
    jr z, .clear
    call DrawChar
    jr .clear
.notgloss:
    cp ST_CARD
    jr nz, .match
    call DrawChar
    jr .clear
.match:
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
    ld a, CHAR_OAM_Y
    ld [wDrawY], a              ; fixed height: the far board hides the lower body
    ld a, e
    sub 8                       ; 32 wide, centred: OAM x = screen x - 16 + 8
    ld [wDrawX], a
; Draw the opponent with its top-left OAM corner at wDrawX/wDrawY: two layers of
; eight 8x16 pieces (layer B on top, palette 4; layer A below, palette 3), tiles
; from VRAM bank 1: frame * 32 + layer * 16 + piece * 2.
DrawCharHere:
    ld a, [wOppAnim]
    and a
    jr z, .idle
    ld a, 32
.idle:
    add 16                      ; start with layer B
    ld [wDrawCount], a          ; current tile
    ld a, 4 | $08
    ld [wDrawAttr], a
    call .layer
    ld a, [wDrawCount]
    sub 32                      ; back to layer A of the same frame
    ld [wDrawCount], a
    ld a, 3 | $08
    ld [wDrawAttr], a
.layer:
    ld b, 0                     ; piece 0..7
.piece:
    ld a, b
    cp 4
    ld a, [wDrawY]
    jr c, .row0
    add 16
.row0:
    ld [hl+], a
    ld a, b
    and 3
    add a
    add a
    add a
    ld c, a
    ld a, [wDrawX]
    add c
    ld [hl+], a
    ld a, [wDrawCount]
    ld [hl+], a
    add 2
    ld [wDrawCount], a
    ld a, [wDrawAttr]
    ld [hl+], a
    inc b
    ld a, b
    cp 8
    jr nz, .piece
    ret

; ---------------------------------------------------------------------------
SECTION "Text", ROM0
TxtStart:   db "    PRESS START     ", $FF
TxtMenuStart: db "      START GAME    ", $FF
TxtMenuGloss: db "      GLOSSARY      ", $FF
TxtMenuHowto: db "      HOW TO PLAY   ", $FF
TxtHowto:   db "    HOW TO PLAY     ", $FF
            db " D-PAD: MOVE PADDLE ", $FF
            db " PUSH INTO A SHOT TO", $FF
            db " HIT HARDER. SLIDE  ", $FF
            db " SIDEWAYS TO ANGLE. ", $FF
            db $FE
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
wMenu::      ds 1
wPage::      ds 1
wGlossWho::  ds 1
wGlossStage:: ds 1
wGlossPtr::  ds 2
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
