; Skydeck Slide -- four-channel music driver
; ch1 pulse harmony, ch2 pulse lead, ch3 wave bass, ch4 noise drums.
; Sound effects borrow ch1 / ch4 for a few frames (wSfxLock1 / wSfxLock4);
; the music keeps time and simply does not write that channel meanwhile.
INCLUDE "hardware.inc"

DEF rNR30 EQU $FF1A
DEF rNR31 EQU $FF1B
DEF rNR32 EQU $FF1C
DEF rNR33 EQU $FF1D
DEF rNR34 EQU $FF1E
DEF WAVE_RAM EQU $FF30

SECTION "Music driver", ROM0

; hl = song header: db tempo, duty1, env1, duty2, env2, vol3 ; dw ch1, ch2, ch3, ch4
PlaySong::
    xor a
    ld [wMusOn], a
    ld a, [hl+]
    ld [wMusTempo], a
    ld a, 1
    ld [wMusTick], a
    ld a, [hl+]
    ld [wMusDuty1], a
    ld a, [hl+]
    ld [wMusEnv1], a
    ld a, [hl+]
    ld [wMusDuty2], a
    ld a, [hl+]
    ld [wMusEnv2], a
    ld a, [hl+]
    ld [wMusVol3], a
    ld de, wMusChan
    ld b, 4
.chan:
    push bc
    ld a, [hl+]
    ld c, a
    ld a, [hl+]
    ld b, a
    ld a, c
    ld [de], a                  ; start
    inc de
    ld a, b
    ld [de], a
    inc de
    ld a, c
    ld [de], a                  ; current position
    inc de
    ld a, b
    ld [de], a
    inc de
    ld a, 1
    ld [de], a                  ; steps left on the current note
    inc de
    pop bc
    dec b
    jr nz, .chan
    call LoadWave
    call SilenceMusic
    ld a, 1
    ld [wMusOn], a
    ret

StopMusic::
    xor a
    ld [wMusOn], a
    ; fall through

SilenceMusic::
    xor a
    ldh [rNR22], a
    ldh [rNR32], a
    ld a, [wSfxLock1]
    and a
    jr nz, .keep1
    ldh [rNR12], a
.keep1:
    ld a, [wSfxLock4]
    and a
    ret nz
    ldh [rNR42], a
    ret

; pause / resume keep the song position
PauseMusic::
    xor a
    ld [wMusOn], a
    jr SilenceMusic

ResumeMusic::
    ld a, 1
    ld [wMusOn], a
    ret

LoadWave:
    xor a
    ldh [rNR30], a
    ld hl, BassWave
    ld de, WAVE_RAM
    ld c, 16
.l:
    ld a, [hl+]
    ld [de], a
    inc de
    dec c
    jr nz, .l
    ret

; a soft, rounded bass wave (32 four-bit samples)
BassWave:
    db $01, $34, $67, $89, $AB, $CD, $EE, $FF, $FF, $EE, $DC, $BA, $98, $76, $43, $10

; called once per frame
MusicUpdate::
    ld hl, wSfxLock1
    ld a, [hl]
    and a
    jr z, .l4
    dec [hl]
.l4:
    ld hl, wSfxLock4
    ld a, [hl]
    and a
    jr z, .locks
    dec [hl]
.locks:
    ld a, [wMusOn]
    and a
    ret z
    ld hl, wMusTick
    dec [hl]
    ret nz
    ld a, [wMusTempo]
    ld [hl], a
    xor a
.each:
    push af
    call StepChannel
    pop af
    inc a
    cp 4
    jr nz, .each
    ret

; a = channel 0..3: count down the current note, read the next event when it ends
StepChannel:
    ld [wMusCh], a
    ld c, a
    add a
    add a
    add c                       ; * 5 bytes per channel
    ld hl, wMusChan
    call AddAtoHL
    push hl
    ld bc, 4
    add hl, bc
    dec [hl]
    pop hl
    ret nz
    inc hl
    inc hl                      ; -> position
    ld a, [hl+]
    ld e, a
    ld d, [hl]                  ; de = position, hl -> position hi
.read:
    ld a, [de]
    cp $FF
    jr nz, .notloop
    dec hl
    dec hl
    dec hl                      ; -> start lo
    ld a, [hl+]
    ld e, a
    ld d, [hl]
    inc hl
    inc hl                      ; -> position hi
    jr .read
.notloop:
    cp $FE
    jr nz, .event
    inc hl
    ld [hl], 255                ; song over: wait as long as possible, then read $FE again
    jp MuteCurrent
.event:
    ld b, a                     ; note
    inc de
    ld a, [de]
    inc de
    ld c, a                     ; length in steps
    ld a, d
    ld [hl-], a
    ld a, e
    ld [hl+], a
    inc hl
    ld [hl], c
    ld a, [wMusCh]
    and a
    jr z, PlayCh1
    dec a
    jr z, PlayCh2
    dec a
    jr z, PlayCh3
    jp PlayCh4

; hl = frequency register value for note b (1-based)
NoteFreq:
    ld a, b
    dec a
    add a
    ld hl, MusicNoteTable
    call AddAtoHL
    ld a, [hl+]
    ld h, [hl]
    ld l, a
    ret

PlayCh1:
    ld a, [wSfxLock1]
    and a
    ret nz
    ld a, b
    and a
    jr z, .rest
    call NoteFreq
    xor a
    ldh [rNR10], a
    ld a, [wMusDuty1]
    ldh [rNR11], a
    ld a, [wMusEnv1]
    ldh [rNR12], a
    ld a, l
    ldh [rNR13], a
    ld a, h
    or $80
    ldh [rNR14], a
    ret
.rest:
    ldh [rNR12], a
    ret

PlayCh2:
    ld a, b
    and a
    jr z, .rest
    call NoteFreq
    ld a, [wMusDuty2]
    ldh [rNR21], a
    ld a, [wMusEnv2]
    ldh [rNR22], a
    ld a, l
    ldh [rNR23], a
    ld a, h
    or $80
    ldh [rNR24], a
    ret
.rest:
    ldh [rNR22], a
    ret

PlayCh3:
    ld a, b
    and a
    jr z, .rest
    call NoteFreq
    ld a, $80
    ldh [rNR30], a
    xor a
    ldh [rNR31], a
    ld a, [wMusVol3]
    ldh [rNR32], a
    ld a, l
    ldh [rNR33], a
    ld a, h
    or $80
    ldh [rNR34], a
    ret
.rest:
    ldh [rNR32], a
    ret

; drums: 1 kick, 2 snare, 3 hi-hat
PlayCh4:
    ld a, [wSfxLock4]
    and a
    ret nz
    ld a, b
    and a
    ret z
    dec a
    add a
    ld hl, DrumTable
    call AddAtoHL
    xor a
    ldh [rNR41], a
    ld a, [hl+]
    ldh [rNR42], a
    ld a, [hl]
    ldh [rNR43], a
    ld a, $80
    ldh [rNR44], a
    ret

DrumTable:      ; envelope, noise shape
    db $B1, $62                 ; kick: loud, low, short
    db $A2, $41                 ; snare: mid, a bit longer
    db $51, $10                 ; hi-hat: quiet, high, very short

MuteCurrent:
    ld a, [wMusCh]
    and a
    jr z, .c1
    dec a
    jr z, .c2
    dec a
    jr z, .c3
    ret
.c1:
    ld a, [wSfxLock1]
    and a
    ret nz
    ldh [rNR12], a
    ret
.c2:
    xor a
    ldh [rNR22], a
    ret
.c3:
    xor a
    ldh [rNR32], a
    ret

SECTION "Music data", ROMX
INCLUDE "music.inc"

SECTION "Music variables", WRAM0
wMusOn::    ds 1
wMusTempo:: ds 1
wMusTick::  ds 1
wMusCh::    ds 1
wMusDuty1:: ds 1
wMusEnv1::  ds 1
wMusDuty2:: ds 1
wMusEnv2::  ds 1
wMusVol3::  ds 1
wMusChan::  ds 4 * 5        ; per channel: start (2), position (2), steps left (1)
wSfxLock1:: ds 1
wSfxLock4:: ds 1
