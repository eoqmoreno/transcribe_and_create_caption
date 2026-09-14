# Transcrever vídeo para texto

Este projeto usa o `faster-whisper` para transcrever o áudio de um vídeo e gerar:

- um arquivo `.txt` com a transcrição e timestamps;
- um arquivo `.srt` para usar como legenda.

O modelo padrão é o `medium`. Ele costuma produzir um resultado melhor que o
`small`, mas pode demorar mais e consumir mais memória.

## Requisitos

- Python 3.9 ou mais recente;
- `ffmpeg` instalado e disponível no `PATH`;
- espaço em disco e internet para baixar o modelo na primeira execução.

O vídeo de entrada deve estar na pasta do projeto ou ser informado com o
caminho completo. O arquivo de vídeo não precisa ser enviado para o GitHub.

## 1. Baixar o projeto

Se o Git estiver instalado, abra o PowerShell no Windows ou o Terminal no macOS
e execute:

```bash
git clone https://github.com/eoqmoreno/transcribe_and_create_caption.git
cd transcribe_and_create_caption
```

Também é possível baixar o projeto como ZIP no GitHub e abrir uma janela de
terminal dentro da pasta extraída.

## 2. Instalação no Windows

### Instalar Python

Baixe o Python em [python.org/downloads](https://www.python.org/downloads/).
Durante a instalação, marque **Add Python to PATH** e conclua o instalador.
Feche e abra o PowerShell novamente e confirme:

```powershell
python --version
```

### Instalar o ffmpeg

No Windows 10 ou 11, o modo mais simples é usar o `winget` no PowerShell:

```powershell
winget install Gyan.FFmpeg.Shared
```

Feche e abra o PowerShell novamente e confirme:

```powershell
ffmpeg -version
```

Se o comando `winget` não estiver disponível, instale o `ffmpeg` por outro
gerenciador, como o [Chocolatey](https://chocolatey.org/install):

```powershell
choco install ffmpeg
```

### Criar o ambiente e instalar as dependências

Na pasta do projeto, execute:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Se o PowerShell bloquear a ativação do ambiente, permita scripts somente nesta
janela e tente novamente:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

O ambiente estará ativo quando `(.venv)` aparecer no início da linha do
PowerShell.

## 3. Instalação no macOS

Abra o Terminal e entre na pasta do projeto:

```bash
cd /caminho/para/transcribe_and_create_caption
```

Instale o `ffmpeg` com o [Homebrew](https://brew.sh/), caso ainda não esteja
instalado:

```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
brew install ffmpeg
ffmpeg -version
```

Em Macs Apple Silicon, se `brew` não for encontrado, siga a instrução mostrada
pelo instalador para adicioná-lo ao `PATH`. Em Macs Intel, o Homebrew costuma
ficar em `/usr/local/bin`.

Crie o ambiente virtual e instale as dependências:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

## 4. Executar a transcrição

Coloque **um único vídeo** dentro da pasta `template/`. O nome do arquivo pode
ser qualquer um, desde que tenha uma extensão de vídeo, como `.mp4`, `.mkv`,
`.avi`, `.mov`, `.webm` ou `.m4v`.

Com o ambiente virtual ativado, execute na pasta principal do projeto:

Windows (PowerShell):

```powershell
python transcribe_video.py
```

macOS (Terminal):

```bash
python transcribe_video.py
```

Os arquivos `.txt` e `.srt` serão criados dentro de `template/`, usando o mesmo
nome do vídeo. Por exemplo, `template/minha-reuniao.mp4` gera:

```text
template/minha-reuniao.txt
template/minha-reuniao.srt
```

Se houver mais de um vídeo na pasta, o programa mostrará os nomes encontrados e
pedirá que você deixe somente um ou informe o arquivo manualmente.

O arquivo `.txt` inclui timestamps por padrão. Para gerar somente o texto:

```bash
python transcribe_video.py template/reuniao.mp4 --no-timestamps
```

Para definir outro nome para a transcrição, informe o segundo argumento. O
arquivo `.srt` usará o mesmo nome base:

```bash
python transcribe_video.py template/reuniao.mp4 template/resultado.txt
```

## Qualidade e velocidade

O modelo pode ser escolhido com `--model`:

| Modelo | Resultado esperado | Uso de recursos |
| --- | --- | --- |
| `small` | bom | menor |
| `medium` | melhor equilíbrio e padrão do projeto | médio/alto |
| `large-v3` | melhor qualidade | alto |

Exemplo para priorizar ainda mais a qualidade:

```bash
python transcribe_video.py template/reuniao.mp4 --model large-v3
```

O idioma padrão é português (`pt`). Para outro idioma, use `--language`, por
exemplo `--language en`. O programa usa CPU por padrão e pode ser mais lento em
vídeos longos.

## Primeira execução

Na primeira execução, o modelo escolhido será baixado automaticamente. Esse
download pode ser grande e a transcrição do primeiro vídeo pode demorar mais;
as execuções seguintes reaproveitam o modelo instalado.

Se aparecer a mensagem `ffmpeg não encontrado`, confirme que este comando
funciona no terminal:

```bash
ffmpeg -version
```
