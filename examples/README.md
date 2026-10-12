# Exemplos

Uma música gerada para cada levada. Cada pasta tem:

- `gramatica.txt`: a sequência gerada pela gramática;
- `cifra.txt`: a cifra montada a partir dela;
- `musica.mid`: o MIDI;
- `musica.flac`: o áudio.

| Pasta | Levada | Andamento | Seção A | Seção B |
|---|---|---|---|---|
| [`bossa-seed-2`](bossa-seed-2) | BOSSA (2/4) | 70 bpm | Lá♭ menor | Sol menor |
| [`blocado-seed-3`](blocado-seed-3) | BLOCADO (2/4) | 90 bpm | Dó maior | Mi♭ maior |
| [`valsa-seed-0`](valsa-seed-0) | VALSA (3/4) | 135 bpm | Mi menor | Fá maior |
| [`djavan-seed-1`](djavan-seed-1) | DJAVAN (4/4) | 75 bpm | Fá menor | Dó♯ maior |
| [`samba-seed-11`](samba-seed-11) | SAMBA (2/4) | 85 bpm | Sol maior | Sol menor |

Para gerar de novo a mesma música, use a semente do nome da pasta. O exemplo
abaixo recria a bossa em `out/seed-2/`:

```bash
cfguitar 2
```

O áudio foi renderizado com o soundfont `Nylon_Guitar.sf2`, o violão de náilon
(programa General MIDI 24) extraído do *Live HQ Natural SoundFont GM V3.0*, de
UnderxPipe1985, licenciado sob CC BY (créditos em
[`soundfonts/README.md`](../soundfonts/README.md)). Com outro soundfont, o
timbre muda.
