; Skydeck Slide -- engine: boot, interrupts, video helpers, text, input, sound
INCLUDE "hardware.inc"
INCLUDE "consts.inc"

SECTION "VBlank vector", ROM0[$40]
    jp VBlankISR

SECTION "Header", ROM0[$100]
    nop
    jp Start
    ds $150 - @, 0              ; rgbfix fills in the header

; ---------------------------------------------------------------------------
SECTION "Boot", ROM0
Start:
    di
    ld sp, $E000
    call LcdOff
    ; OAM DMA routine into HRAM
    ld hl, DmaRoutine
    ld de, hOAMDMA
    ld c, DmaRoutineEnd - DmaRoutine
.dma:
    ld a, [hl+]
    ld [de], a
    inc de
    dec c
    jr nz, .dma
    ; clear work RAM below the stack page
    ld hl, $C000
    ld bc, $DF00 - $C000
    xor a
    call Fill
    xor a
    ldh [hJoyHeld], a
    ldh [hJoyPressed], a
    ldh [hVBlankFlag], a
    ldh [rSCX], a
    ldh [rSCY], a
    ld a, 77
    ld [wSeed], a
    call SoundInit
    ; sprite palettes (background palettes are loaded with each screen)
    ld hl, ObjPalettes
    ld a, $80
    ldh [rOCPS], a
    ld c, 64
.obp:
    ld a, [hl+]
    ldh [rOCPD], a
    dec c
    jr nz, .obp
    ; font into VRAM bank 0 at $9000 (BG tiles 0..)
    xor a
    ldh [rVBK], a
    ld hl, FontTiles
    ld de, $9000
    ld bc, FontTilesEnd - FontTiles
    call Copy
    ; sprite tiles into VRAM bank 0 at $8000
    ld hl, ObjTiles
    ld de, $8000
    ld bc, ObjTilesEnd - ObjTiles
    call Copy

    call EnterTitle
    ld a, 1
    ldh [rIE], a
    xor a
    ldh [rIF], a
    ei
MainLoop:
    call WaitVBlank
    call FlushRow
    call MusicUpdate
    call ReadJoypad
    call RunState
    call DrawSprites
    jr MainLoop

DmaRoutine:
    ld a, HIGH(wShadowOAM)
    ldh [rDMA], a
    ld a, 40
.wait:
    dec a
    jr nz, .wait
    ret
DmaRoutineEnd:

VBlankISR:
    push af
    call hOAMDMA
    ld a, 1
    ldh [hVBlankFlag], a
    pop af
    reti

; ---------------------------------------------------------------------------
SECTION "Utilities", ROM0
WaitVBlank::
    xor a
    ldh [hVBlankFlag], a
.wait:
    halt
    ldh a, [hVBlankFlag]
    and a
    jr z, .wait
    ret

; turn the LCD off safely (only during vblank)
LcdOff::
    ldh a, [rLCDC]
    bit 7, a
    ret z
.wait:
    ldh a, [rLY]
    cp 144
    jr c, .wait
    xor a
    ldh [rLCDC], a
    ret

LcdOn::
    ld a, LCDC_GAME
    ldh [rLCDC], a
    ret

; copy bc bytes from hl to de
Copy::
    ld a, [hl+]
    ld [de], a
    inc de
    dec bc
    ld a, b
    or c
    jr nz, Copy
    ret

; fill bc bytes at hl with a
Fill::
    ld d, a
.loop:
    ld a, d
    ld [hl+], a
    dec bc
    ld a, b
    or c
    jr nz, .loop
    ret

; load a screen: hl = tile chunk list, then map and attributes follow via de / bc
; chunk list: db bank, dw address, dw tile count, data...; db $FF ends it
LoadChunks::
.next:
    ld a, [hl+]
    cp $FF
    jr z, .done
    ldh [rVBK], a
    ld a, [hl+]
    ld e, a
    ld a, [hl+]
    ld d, a
    ld a, [hl+]
    ld c, a
    ld a, [hl+]
    ld b, a
    ; bytes = tiles * 16
    sla c
    rl b
    sla c
    rl b
    sla c
    rl b
    sla c
    rl b
    call Copy
    jr .next
.done:
    xor a
    ldh [rVBK], a
    ret

; copy a 20x18 map (hl) into $9800 on VRAM bank a
LoadMap::
    ldh [rVBK], a
    ld de, $9800
    ld b, 18
.row:
    ld c, 20
.col:
    ld a, [hl+]
    ld [de], a
    inc de
    dec c
    jr nz, .col
    ld a, e
    add 12
    ld e, a
    jr nc, .nc
    inc d
.nc:
    dec b
    jr nz, .row
    xor a
    ldh [rVBK], a
    ret

; hl = 8 background palettes
LoadBgPalettes::
    ld a, $80
    ldh [rBCPS], a
    ld c, 64
.loop:
    ld a, [hl+]
    ldh [rBCPD], a
    dec c
    jr nz, .loop
    ret

; load the stage for the current opponent (LCD must be off)
LoadGameScreen::
    ld a, [wLevel]
    call LoadScreen
    ; HUD row: blank text tiles, text palette
    ld hl, $9800
    ld bc, 20
    ld a, CHAR_SPACE
    call Fill
    ld a, 1
    ldh [rVBK], a
    ld hl, $9800
    ld bc, 20
    ld a, TEXT_PALETTE
    call Fill
    xor a
    ldh [rVBK], a
    ret

LoadTitleScreen::
    ld a, TITLE_SCREEN
    ; fall through

; a = StageTable entry: switch to its ROM bank, load palettes, tiles, map, attributes
LoadScreen::
    ld c, a
    add a
    add a
    add a
    add c                       ; 9 bytes per entry
    ld hl, StageTable
    add l
    ld l, a
    adc h
    sub l
    ld h, a
    ld a, [hl+]
    ld [$2000], a               ; MBC5: select the screen's ROM bank
    ld de, wStagePtrs
    ld c, 8
.copy:
    ld a, [hl+]
    ld [de], a
    inc de
    dec c
    jr nz, .copy
    ld hl, wStagePtrs
    call .ptr
    call LoadBgPalettes
    ld hl, wStagePtrs + 2
    call .ptr
    call LoadChunks
    ld hl, wStagePtrs + 4
    call .ptr
    xor a
    call LoadMap
    ld hl, wStagePtrs + 6
    call .ptr
    ld a, 1
    jp LoadMap
.ptr:                           ; hl = the word stored at hl
    ld a, [hl+]
    ld h, [hl]
    ld l, a
    ret

; write a $FF-terminated string at hl into VRAM at de with palette b (LCD off only)
PrintDirect::
    ld a, [hl+]
    cp $FF
    ret z
    ld [de], a
    ld a, 1
    ldh [rVBK], a
    ld a, b
    ld [de], a
    xor a
    ldh [rVBK], a
    inc de
    jr PrintDirect

; ---------------------------------------------------------------------------
; one text row (20 tiles) can be queued per frame and is written in vblank
SetRowFromString::      ; hl = $FF-terminated string (max 20), de = VRAM address
    ld a, e
    ld [wRowAddr], a
    ld a, d
    ld [wRowAddr + 1], a
    ld de, wRowBuf
    ld c, 20
.copy:
    ld a, [hl+]
    cp $FF
    jr z, .pad
    ld [de], a
    inc de
    dec c
    jr nz, .copy
    jr .done
.pad:
    ld a, CHAR_SPACE
.padl:
    ld [de], a
    inc de
    dec c
    jr nz, .padl
.done:
    ld a, 1
    ld [wRowDirty], a
    ret

FlushRow::
    ld a, [wRowDirty]
    and a
    ret z
    xor a
    ld [wRowDirty], a
    ld a, [wRowAddr]
    ld e, a
    ld a, [wRowAddr + 1]
    ld d, a
    ld hl, wRowBuf
    ld c, 20
.loop:
    ld a, [hl+]
    ld [de], a
    inc de
    dec c
    jr nz, .loop
    ret

; ---------------------------------------------------------------------------
ReadJoypad::
    ld a, $20               ; d-pad
    ldh [rP1], a
    ldh a, [rP1]
    ldh a, [rP1]
    cpl
    and $0F
    swap a
    ld b, a
    ld a, $10               ; buttons
    ldh [rP1], a
    ldh a, [rP1]
    ldh a, [rP1]
    ldh a, [rP1]
    ldh a, [rP1]
    cpl
    and $0F
    or b
    ld b, a
    ld a, $30
    ldh [rP1], a
    ldh a, [hJoyHeld]
    cpl
    and b
    ldh [hJoyPressed], a
    ld a, b
    ldh [hJoyHeld], a
    ret

; a = pseudo-random byte
Random::
    push bc
    ld a, [wSeed]
    ld b, a
    add a
    add a
    add b
    inc a
    ld [wSeed], a
    ld b, a
    ldh a, [rDIV]
    xor b
    pop bc
    ret

; hl = a * e (unsigned), clobbers c, d
Mul8::
    ld hl, 0
    ld d, h
    ld c, 8
.loop:
    add hl, hl
    add a
    jr nc, .skip
    add hl, de
.skip:
    dec c
    jr nz, .loop
    ret

; de = -de
NegDE::
    ld a, e
    cpl
    ld e, a
    ld a, d
    cpl
    ld d, a
    inc de
    ret

; [hl] (16-bit) += de
AddWordAtHL::
    ld a, [hl]
    add e
    ld [hl+], a
    ld a, [hl]
    adc d
    ld [hl-], a
    ret

; ---------------------------------------------------------------------------
SoundInit::
    ld a, $80
    ldh [rNR52], a
    ld a, $77
    ldh [rNR50], a
    ld a, $FF
    ldh [rNR51], a
    ret

; Sound effects play on channel 1 (and 4 for the goal) and lock that channel
; against the music for a few frames.
SfxHit::
    ld a, [wSilent]
    and a
    ret nz
    ld a, 10
    ld [wSfxLock1], a
    xor a
    ldh [rNR10], a
    ld a, $80
    ldh [rNR11], a
    ld a, $F2
    ldh [rNR12], a
    ld a, $A0
    ldh [rNR13], a
    ld a, $87
    ldh [rNR14], a
    ret

SfxOppHit::
    ld a, [wSilent]
    and a
    ret nz
    ld a, 10
    ld [wSfxLock1], a
    xor a
    ldh [rNR10], a
    ld a, $80
    ldh [rNR11], a
    ld a, $D2
    ldh [rNR12], a
    ld a, $20
    ldh [rNR13], a
    ld a, $87
    ldh [rNR14], a
    ret

SfxWall::
    ld a, [wSilent]
    and a
    ret nz
    ld a, 6
    ld [wSfxLock1], a
    xor a
    ldh [rNR10], a
    ld a, $40
    ldh [rNR11], a
    ld a, $A1
    ldh [rNR12], a
    ld a, $C0
    ldh [rNR13], a
    ld a, $86
    ldh [rNR14], a
    ret

SfxGoal::
    ld a, 40
    ld [wSfxLock1], a
    ld [wSfxLock4], a
    xor a
    ldh [rNR41], a
    ld a, $F5
    ldh [rNR42], a
    ld a, $64
    ldh [rNR43], a
    ld a, $80
    ldh [rNR44], a
    ld a, $16
    ldh [rNR10], a
    ld a, $80
    ldh [rNR11], a
    ld a, $F4
    ldh [rNR12], a
    ld a, $00
    ldh [rNR13], a
    ld a, $86
    ldh [rNR14], a
    ret

SfxBlip::
    ld a, 8
    ld [wSfxLock1], a
    xor a
    ldh [rNR10], a
    ld a, $80
    ldh [rNR11], a
    ld a, $81
    ldh [rNR12], a
    ld a, $D0
    ldh [rNR13], a
    ld a, $87
    ldh [rNR14], a
    ret

; ---------------------------------------------------------------------------
SECTION "Assets", ROM0
INCLUDE "assets.inc"
INCLUDE "assets_screens.inc"

; ---------------------------------------------------------------------------
SECTION "Shadow OAM", WRAM0, ALIGN[8]
wShadowOAM:: ds 160

SECTION "Variables", WRAM0
wSeed::      ds 1
wSilent::    ds 1
wRowDirty::  ds 1
wRowAddr::   ds 2
wRowBuf::    ds 20
wStagePtrs:: ds 8

SECTION "HRAM", HRAM
hOAMDMA::      ds DmaRoutineEnd - DmaRoutine
hVBlankFlag::  ds 1
hJoyHeld::     ds 1
hJoyPressed::  ds 1
