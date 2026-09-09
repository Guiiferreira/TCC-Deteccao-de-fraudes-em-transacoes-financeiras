const {
  Document, Packer, Paragraph, TextRun, HeadingLevel, AlignmentType,
  Table, TableRow, TableCell, WidthType, BorderStyle, ImageRun,
  PageNumber, Header, Footer, TabStopType, TabStopPosition,
  TableOfContents, PageBreak, ShadingType, VerticalAlign, convertInchesToTwip,
} = require("docx");
const fs = require("fs");

// ---------- Constantes de estilo ABNT ----------
const FONT = "Times New Roman";
const SIZE_BODY = 24;      // 12pt (docx usa half-points)
const SIZE_H1 = 28;        // 14pt
const SIZE_H2 = 24;        // 12pt
const SIZE_H3 = 24;        // 12pt
const SIZE_CAPA_TITLE = 28; // 14pt
const LINE_SPACING_15 = 360; // 1.5 linhas (240 = simples)
const FIRST_LINE_INDENT = 709; // 1,25cm em twips (aprox.)

const MARGIN = {
  top: convertInchesToTwip(1.18),    // 3 cm
  bottom: convertInchesToTwip(0.79), // 2 cm
  left: convertInchesToTwip(1.18),   // 3 cm
  right: convertInchesToTwip(0.79),  // 2 cm
};

function bodyPara(text, opts = {}) {
  return new Paragraph({
    alignment: AlignmentType.JUSTIFIED,
    spacing: { line: LINE_SPACING_15, after: 200 },
    indent: opts.noIndent ? undefined : { firstLine: FIRST_LINE_INDENT },
    children: Array.isArray(text) ? text : [new TextRun({ text, font: FONT, size: SIZE_BODY })],
    ...opts.paraProps,
  });
}

function h1(text, numbering) {
  return new Paragraph({
    heading: HeadingLevel.HEADING_1,
    spacing: { before: 480, after: 240, line: LINE_SPACING_15 },
    children: [new TextRun({ text: text.toUpperCase(), bold: true, font: FONT, size: SIZE_H1, color: "000000" })],
    pageBreakBefore: true,
  });
}

function h2(text) {
  return new Paragraph({
    heading: HeadingLevel.HEADING_2,
    spacing: { before: 360, after: 200, line: LINE_SPACING_15 },
    children: [new TextRun({ text, bold: true, font: FONT, size: SIZE_H2, color: "000000" })],
  });
}

function h3(text) {
  return new Paragraph({
    heading: HeadingLevel.HEADING_3,
    spacing: { before: 280, after: 160, line: LINE_SPACING_15 },
    children: [new TextRun({ text, bold: true, italics: true, font: FONT, size: SIZE_H3, color: "000000" })],
  });
}

function bullet(text) {
  return new Paragraph({
    bullet: { level: 0 },
    alignment: AlignmentType.JUSTIFIED,
    spacing: { line: LINE_SPACING_15, after: 100 },
    children: [new TextRun({ text, font: FONT, size: SIZE_BODY })],
  });
}

function figCaption(text) {
  return new Paragraph({
    alignment: AlignmentType.CENTER,
    spacing: { before: 120, after: 60 },
    children: [new TextRun({ text, italics: true, font: FONT, size: SIZE_BODY })],
  });
}

function fonteText(text) {
  return new Paragraph({
    alignment: AlignmentType.CENTER,
    spacing: { after: 240 },
    children: [new TextRun({ text, font: FONT, size: SIZE_BODY })],
  });
}

function cell(text, opts = {}) {
  return new TableCell({
    width: opts.width ? { size: opts.width, type: WidthType.DXA } : undefined,
    verticalAlign: VerticalAlign.CENTER,
    shading: opts.header ? { type: ShadingType.CLEAR, fill: "1a3a5c" } : undefined,
    margins: { top: 80, bottom: 80, left: 100, right: 100 },
    children: [
      new Paragraph({
        alignment: opts.center ? AlignmentType.CENTER : AlignmentType.LEFT,
        spacing: { line: 276 },
        children: [
          new TextRun({
            text,
            font: FONT,
            size: 20, // 10pt para tabelas (comum em ABNT para caber conteúdo)
            bold: !!opts.header,
            color: opts.header ? "FFFFFF" : undefined,
          }),
        ],
      }),
    ],
  });
}

function refPara(text) {
  return new Paragraph({
    alignment: AlignmentType.JUSTIFIED,
    spacing: { after: 200, line: 240 },
    children: parseBoldMarkup(text),
  });
}

// Interpreta **negrito** dentro de uma string simples, devolvendo TextRuns
function parseBoldMarkup(text) {
  const parts = text.split(/(\*\*[^*]+\*\*)/g);
  return parts.filter(p => p.length > 0).map(p => {
    if (p.startsWith("**") && p.endsWith("**")) {
      return new TextRun({ text: p.slice(2, -2), bold: true, font: FONT, size: SIZE_BODY });
    }
    return new TextRun({ text: p, font: FONT, size: SIZE_BODY });
  });
}

// ---------- CAPA ----------
const capa = [
  new Paragraph({ spacing: { after: 2000 }, children: [] }),
  new Paragraph({
    alignment: AlignmentType.CENTER,
    spacing: { after: 200 },
    children: [new TextRun({ text: "ÂNIMA EDUCAÇÃO", font: FONT, size: SIZE_BODY, bold: true })],
  }),
  new Paragraph({
    alignment: AlignmentType.CENTER,
    spacing: { after: 2000 },
    children: [new TextRun({ text: "Curso de Bacharelado em Engenharia", font: FONT, size: SIZE_BODY })],
  }),
  new Paragraph({
    alignment: AlignmentType.CENTER,
    spacing: { after: 200 },
    children: [new TextRun({ text: "DOCUMENTO DE ESPECIFICAÇÃO DE SOFTWARE", font: FONT, size: SIZE_CAPA_TITLE, bold: true })],
  }),
  new Paragraph({
    alignment: AlignmentType.CENTER,
    spacing: { after: 2400 },
    children: [new TextRun({ text: "SISTEMA DE DETECÇÃO DE FRAUDE EM TRANSAÇÕES FINANCEIRAS", font: FONT, size: SIZE_CAPA_TITLE, bold: true })],
  }),
  new Paragraph({
    alignment: AlignmentType.CENTER,
    spacing: { after: 200 },
    children: [new TextRun({ text: "Equipe de Desenvolvimento:", font: FONT, size: SIZE_BODY })],
  }),
  new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 100 }, children: [new TextRun({ text: "[Nome do(a) integrante 1]", font: FONT, size: SIZE_BODY })] }),
  new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 100 }, children: [new TextRun({ text: "[Nome do(a) integrante 2]", font: FONT, size: SIZE_BODY })] }),
  new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 100 }, children: [new TextRun({ text: "[Nome do(a) integrante 3]", font: FONT, size: SIZE_BODY })] }),
  new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 100 }, children: [new TextRun({ text: "[Nome do(a) integrante 4]", font: FONT, size: SIZE_BODY })] }),
  new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 100 }, children: [new TextRun({ text: "[Nome do(a) integrante 5]", font: FONT, size: SIZE_BODY })] }),
  new Paragraph({ spacing: { after: 3000 }, children: [] }),
  new Paragraph({
    alignment: AlignmentType.CENTER,
    spacing: { after: 60 },
    children: [new TextRun({ text: "[Cidade]", font: FONT, size: SIZE_BODY })],
  }),
  new Paragraph({
    alignment: AlignmentType.CENTER,
    children: [new TextRun({ text: "2026", font: FONT, size: SIZE_BODY })],
    pageBreakAfter: true,
  }),
];

// ---------- FOLHA DE ROSTO ----------
const folhaRosto = [
  new Paragraph({ spacing: { after: 2400 }, children: [] }),
  new Paragraph({
    alignment: AlignmentType.CENTER,
    spacing: { after: 2400 },
    children: [new TextRun({ text: "SISTEMA DE DETECÇÃO DE FRAUDE EM TRANSAÇÕES FINANCEIRAS", font: FONT, size: SIZE_CAPA_TITLE, bold: true })],
  }),
  new Paragraph({
    alignment: AlignmentType.JUSTIFIED,
    indent: { left: 4500 },
    spacing: { line: LINE_SPACING_15, after: 200 },
    children: [new TextRun({
      text: "Documento de especificação de software apresentado como parte do Trabalho de Conclusão de Curso (TCC) em Engenharia, com a finalidade de especificar e documentar o sistema desenvolvido pelo grupo.",
      font: FONT, size: SIZE_BODY,
    })],
  }),
  new Paragraph({
    alignment: AlignmentType.JUSTIFIED,
    indent: { left: 4500 },
    spacing: { after: 2400, line: LINE_SPACING_15 },
    children: [new TextRun({ text: "Orientador: Prof. Nelson Aguiar", font: FONT, size: SIZE_BODY })],
  }),
  new Paragraph({ spacing: { after: 3000 }, children: [] }),
  new Paragraph({
    alignment: AlignmentType.CENTER,
    spacing: { after: 60 },
    children: [new TextRun({ text: "[Cidade]", font: FONT, size: SIZE_BODY })],
  }),
  new Paragraph({
    alignment: AlignmentType.CENTER,
    children: [new TextRun({ text: "2026", font: FONT, size: SIZE_BODY })],
    pageBreakAfter: true,
  }),
];

// ---------- SUMÁRIO ----------
const sumario = [
  new Paragraph({
    heading: HeadingLevel.HEADING_1,
    spacing: { after: 400 },
    children: [new TextRun({ text: "SUMÁRIO", bold: true, font: FONT, size: SIZE_H1, color: "000000" })],
  }),
  new TableOfContents("Sumário", {
    hyperlink: true,
    headingStyleRange: "1-3",
  }),
  new Paragraph({ children: [], pageBreakAfter: true }),
];

// ---------- NOTA DE ACOMPANHAMENTO ----------
const notaAcompanhamento = [
  new Table({
    width: { size: 100, type: WidthType.PERCENTAGE },
    borders: {
      top: { style: BorderStyle.SINGLE, size: 4, color: "1a3a5c" },
      bottom: { style: BorderStyle.SINGLE, size: 4, color: "1a3a5c" },
      left: { style: BorderStyle.SINGLE, size: 4, color: "1a3a5c" },
      right: { style: BorderStyle.SINGLE, size: 4, color: "1a3a5c" },
    },
    rows: [
      new TableRow({
        children: [
          new TableCell({
            shading: { type: ShadingType.CLEAR, fill: "f5f0e6" },
            margins: { top: 150, bottom: 150, left: 150, right: 150 },
            children: [
              new Paragraph({
                spacing: { after: 100 },
                children: [new TextRun({ text: "NOTA DE ACOMPANHAMENTO (remover antes da entrega final)", bold: true, font: FONT, size: SIZE_BODY })],
              }),
              new Paragraph({
                alignment: AlignmentType.JUSTIFIED,
                spacing: { line: LINE_SPACING_15 },
                children: [new TextRun({
                  text: "Este documento está sendo construído de forma incremental, seguindo o cronograma de entregas definido pelo professor orientador. Capítulos ainda não desenvolvidos aparecem marcados como \"A DESENVOLVER\", com a respectiva data de entrega prevista.",
                  font: FONT, size: SIZE_BODY,
                })],
              }),
            ],
          }),
        ],
      }),
    ],
  }),
  new Paragraph({ spacing: { after: 300 }, children: [] }),
];

// ---------- CAPÍTULO 1 — INTRODUÇÃO ----------
const cap1 = [
  h1("1 Introdução"),
  h2("1.1 Contextualização"),
  bodyPara("O avanço da digitalização dos meios de pagamento mudou a forma como transações financeiras acontecem no Brasil. A popularização do Pix, o crescimento do comércio eletrônico e a expansão de fintechs ampliaram o acesso da população a serviços financeiros — e, junto com isso, abriram espaço para o crescimento das fraudes financeiras."),
  bodyPara("Dados recentes mostram a dimensão do problema. Segundo levantamento da Quod, com base no Registro Unificado de Fraudes (Rufra), o Brasil registrou mais de 9 milhões de indícios de fraudes financeiras apenas no primeiro semestre de 2026, um crescimento de 10,26% em relação ao segundo semestre de 2025. Contas correntes estiveram envolvidas em 94% dos indícios registrados, celulares em 78%, e o Pix foi o meio de pagamento usado em 85% dos casos. A engenharia social respondeu por 40% dos golpes, com cerca de 3,1 milhões de vítimas (AGÊNCIA BRASIL, 2026)."),
  bodyPara("No campo mais restrito das fraudes em cartão de crédito e comércio eletrônico — recorte de maior relevância para este trabalho — o cenário é igualmente preocupante. O prejuízo estimado com fraudes em compras online por cartão de crédito saltou de R$ 3,9 bilhões em 2020 para R$ 7,8 bilhões em 2025, com projeção de R$ 8,1 bilhões para 2026 (BAND, 2026). Em levantamento anterior, de aproximadamente 280 milhões de transações de cartão em e-commerce, 3,7 milhões (1,4% do total) foram identificadas como tentativas fraudulentas, com perdas da ordem de R$ 3,5 bilhões (PAGBRASIL, 2024). A Serasa Experian, por sua vez, registrou 6.937.832 tentativas de fraude no primeiro semestre de 2025 — alta de 29,5% frente ao mesmo período do ano anterior (SINCOMAVI; SERASA EXPERIAN, 2025)."),
  bodyPara("Parte desse crescimento nos números reportados não vem só do aumento da atividade criminosa: vem também de mecanismos de detecção melhores e do maior compartilhamento de dados entre instituições financeiras, impulsionado pela Resolução nº 501 do Banco Central (AGÊNCIA BRASIL, 2026). Ainda assim, o volume de dados a processar e a sutileza dos padrões de fraude seguem exigindo ferramentas capazes de identificá-los em tempo hábil."),
  bodyPara("Há também um desafio técnico relevante: bases de dados de transações financeiras são, por natureza, altamente desbalanceadas — a fração de transações fraudulentas é ínfima diante do total de transações legítimas. Esse desbalanceamento compromete algoritmos de classificação tradicionais, que tendem a favorecer a classe majoritária e deixar passar despercebidos justamente os casos que um sistema antifraude deveria identificar."),

  h2("1.2 Justificativa"),
  bodyPara("Apesar da disponibilidade de soluções antifraude no mercado, essas ferramentas costumam ser acessíveis principalmente a grandes instituições financeiras, que dispõem de orçamento e infraestrutura tecnológica para implementá-las. Pequenas fintechs e varejistas digitais, por outro lado, frequentemente carecem de mecanismos acessíveis e eficazes para identificar transações fraudulentas em tempo real, ficando mais expostos a prejuízos financeiros diretos e a danos à confiança de seus clientes."),
  bodyPara("É desse contexto que parte o cenário deste trabalho:"),
  bodyPara([new TextRun({ text: "Problema: ", bold: true, font: FONT, size: SIZE_BODY }), new TextRun({ text: "pequenas fintechs e empresas de comércio eletrônico possuem dificuldade em identificar, de forma acessível e em tempo real, transações financeiras fraudulentas, o que resulta em prejuízos financeiros e perda de confiança dos consumidores.", font: FONT, size: SIZE_BODY })]),
  bodyPara([new TextRun({ text: "Solução proposta: ", bold: true, font: FONT, size: SIZE_BODY }), new TextRun({ text: "o desenvolvimento de um sistema inteligente capaz de analisar transações financeiras e classificá-las automaticamente quanto ao risco de fraude, utilizando algoritmos de Machine Learning — especificamente Regressão Logística, Árvore de Decisão e Random Forest —, com tratamento adequado do desbalanceamento de classes, permitindo a comparação de desempenho entre os modelos e a identificação da abordagem mais eficaz para o contexto proposto.", font: FONT, size: SIZE_BODY })]),
  bodyPara([new TextRun({ text: "A partir desse cenário, a pesquisa busca responder a uma questão central: ", font: FONT, size: SIZE_BODY }), new TextRun({ text: "qual algoritmo de Machine Learning apresenta melhor desempenho na detecção de fraudes financeiras em bases de dados altamente desbalanceadas?", bold: true, font: FONT, size: SIZE_BODY })]),
  bodyPara("A relevância do trabalho aparece em mais de uma frente. Há o impacto econômico e social crescente das fraudes financeiras no Brasil, evidenciado pelos dados da contextualização, que atinge tanto instituições financeiras quanto milhões de consumidores. Há também uma lacuna real de ferramentas antifraude acessíveis para pequenas e médias empresas do setor financeiro e do comércio eletrônico — público que as soluções corporativas de grande porte costumam deixar de fora. E há o problema técnico-científico da classificação em bases desbalanceadas, tema recorrente na literatura de aprendizado de máquina, que pede comparação empírica entre abordagens diferentes para se chegar a conclusões consistentes sobre qual estratégia funciona melhor em contextos parecidos."),
  bodyPara("Do ponto de vista acadêmico, o projeto também serve como aplicação prática de conceitos de engenharia de requisitos, aprendizado de máquina, arquitetura de software e gestão ágil — e a documentação funciona como o principal canal de comunicação entre a equipe e o professor orientador."),

  h2("1.3 Objetivos"),
  h3("1.3.1 Objetivo geral"),
  bodyPara("Desenvolver e avaliar um sistema de classificação de fraudes em transações financeiras baseado em algoritmos de Machine Learning, comparando o desempenho de diferentes modelos em um cenário de dados altamente desbalanceados."),
  h3("1.3.2 Objetivos específicos"),
  bullet("Realizar revisão bibliográfica sobre fraudes financeiras no Brasil, técnicas de Machine Learning aplicadas à detecção de fraude e métodos de tratamento de desbalanceamento de classes;"),
  bullet("Levantar e descrever os requisitos funcionais e não funcionais do sistema;"),
  bullet("Representar, por meio de diagrama de casos de uso, as interações entre os atores e o sistema;"),
  bullet("Treinar e comparar os algoritmos de Regressão Logística, Árvore de Decisão e Random Forest sobre uma base pública de transações de cartão de crédito;"),
  bullet("Aplicar e avaliar técnicas de balanceamento de classes sobre os modelos treinados;"),
  bullet("Avaliar o desempenho dos algoritmos por meio de métricas adequadas a cenários desbalanceados — precisão, recall, F1-score e AUC-ROC;"),
  bullet("Desenvolver um serviço de inferência que permita a classificação de transações em tempo real, com painel de alertas para revisão humana dos casos sinalizados como suspeitos;"),
  bullet("Modelar a estrutura estática do sistema por meio de diagrama de classes e o comportamento dinâmico de um dos principais fluxos por meio de diagrama de sequência;"),
  bullet("Definir a arquitetura de software em camadas e as tecnologias associadas a cada camada."),
];

// ---------- CAPÍTULO 2 — REQUISITOS DO SISTEMA ----------
const imagePath = "diagramas/diagrama_casos_uso.png";
const imageBuffer = fs.readFileSync(imagePath);

const tabelaAtores = new Table({
  width: { size: 100, type: WidthType.PERCENTAGE },
  rows: [
    new TableRow({ tableHeader: true, children: [cell("Ator", { header: true, width: 2500 }), cell("Descrição", { header: true, width: 6500 })] }),
    new TableRow({ children: [cell("Sistema Externo (Plataforma de Pagamento)"), cell("Sistema automatizado (ex.: plataforma de e-commerce ou fintech) que envia os dados de uma transação para classificação em tempo real via API.")] }),
    new TableRow({ children: [cell("Analista de Fraude"), cell("Profissional responsável por consultar os alertas gerados pelo sistema, revisar manualmente cada caso e classificá-lo como \"fraude confirmada\" ou \"falso positivo\".")] }),
    new TableRow({ children: [cell("Cientista de Dados"), cell("Responsável por treinar e comparar os modelos de classificação, avaliando suas métricas de desempenho antes de colocá-los em produção.")] }),
  ],
});

const tabelaCasosUso = new Table({
  width: { size: 100, type: WidthType.PERCENTAGE },
  rows: [
    new TableRow({ tableHeader: true, children: [cell("ID", { header: true, width: 900 }), cell("Caso de uso", { header: true, width: 3600 }), cell("Ator(es) principal(is)", { header: true, width: 4500 })] }),
    new TableRow({ children: [cell("UC01", { center: true }), cell("Treinar modelo de classificação"), cell("Cientista de Dados")] }),
    new TableRow({ children: [cell("UC02", { center: true }), cell("Classificar transação"), cell("Sistema Externo")] }),
    new TableRow({ children: [cell("UC03", { center: true }), cell("Consultar transações"), cell("Analista de Fraude")] }),
    new TableRow({ children: [cell("UC04", { center: true }), cell("Consultar alertas"), cell("Analista de Fraude")] }),
    new TableRow({ children: [cell("UC05", { center: true }), cell("Revisar alerta"), cell("Analista de Fraude")] }),
    new TableRow({ children: [cell("UC06", { center: true }), cell("Consultar métricas do modelo"), cell("Analista de Fraude, Cientista de Dados")] }),
    new TableRow({ children: [cell("UC07", { center: true }), cell("Autenticar-se (API Key)"), cell("(incluído pelos demais casos de uso)")] }),
  ],
});

const rfRows = [
  ["RF01", "O sistema deve treinar o modelo de classificação a partir do dataset público, persistindo o modelo treinado (ex: .pkl) de forma versionada.", "UC01", "Essencial"],
  ["RF02", "O sistema deve expor um endpoint POST /transacoes/classificar que recebe os atributos de uma transação e retorna score de risco e classe prevista.", "UC02", "Essencial"],
  ["RF03", "O sistema deve armazenar toda transação classificada com seu score, classe prevista e timestamp no banco de dados.", "UC02", "Essencial"],
  ["RF04", "O sistema deve listar no painel as transações com score acima de um limiar configurável (ex: 0,7) como \"alerta\".", "UC04", "Essencial"],
  ["RF05", "O sistema deve permitir que o analista marque um alerta como \"fraude confirmada\" ou \"falso positivo\".", "UC05", "Essencial"],
  ["RF06", "O sistema deve calcular e exibir métricas do modelo (precisão, recall, F1, matriz de confusão) e volume de alertas por dia.", "UC06", "Importante"],
  ["RF07", "O sistema deve permitir filtrar transações/alertas por intervalo de datas, valor mínimo/máximo e status de revisão.", "UC03, UC04", "Importante"],
];

const tabelaRF = new Table({
  width: { size: 100, type: WidthType.PERCENTAGE },
  rows: [
    new TableRow({ tableHeader: true, children: [
      cell("ID", { header: true, width: 700 }),
      cell("Descrição", { header: true, width: 5200 }),
      cell("Caso de uso", { header: true, width: 1400 }),
      cell("Prioridade", { header: true, width: 1500 }),
    ] }),
    ...rfRows.map(([id, desc, uc, prio]) => new TableRow({
      children: [cell(id, { center: true }), cell(desc), cell(uc, { center: true }), cell(prio, { center: true })],
    })),
  ],
});

const cap2 = [
  h1("2 Requisitos do Sistema"),
  bodyPara("Este capítulo apresenta o levantamento de requisitos do sistema, iniciando pela identificação dos atores e casos de uso (Seção 2.1), seguida da listagem dos requisitos funcionais, priorizados segundo a classificação MoSCoW (Seção 2.2). O detalhamento dos fluxos de cada caso de uso e os requisitos não funcionais serão apresentados nas próximas entregas (ver notas de acompanhamento ao final do documento)."),

  h2("2.1 Diagrama de casos de uso"),
  bodyPara("A Figura 1 apresenta o diagrama de casos de uso do sistema, elaborado segundo a notação UML (Unified Modeling Language). Foram identificados três atores principais: Sistema Externo (plataforma de pagamento ou comércio eletrônico que envia transações para análise), Analista de Fraude (responsável pela revisão manual dos alertas gerados) e Cientista de Dados (responsável pelo treinamento e acompanhamento do modelo de Machine Learning)."),

  new Paragraph({
    alignment: AlignmentType.CENTER,
    spacing: { before: 200, after: 60 },
    children: [
      new ImageRun({
        data: imageBuffer,
        transformation: { width: 500, height: (500 * 973) / 1215 },
        type: "png",
      }),
    ],
  }),
  figCaption("Figura 1 — Diagrama de casos de uso do sistema"),
  fonteText("Fonte: elaborado pelos autores (2026)"),

  bodyPara("Todos os casos de uso que expõem dados de transações — UC02 a UC06 — incluem (<<include>>) o caso de uso UC07 (Autenticar-se), já que o sistema exige autenticação por chave de API para acesso a qualquer dado sensível, conforme requisito não funcional de segurança (a ser detalhado na Seção 2.4)."),

  h3("2.1.1 Descrição resumida dos atores"),
  tabelaAtores,
  new Paragraph({ spacing: { after: 300 }, children: [] }),

  h3("2.1.2 Descrição resumida dos casos de uso"),
  tabelaCasosUso,
  new Paragraph({ spacing: { after: 300 }, children: [] }),

  h2("2.2 Requisitos funcionais"),
  bodyPara("Os requisitos funcionais (RF) descrevem as funcionalidades que o sistema deve disponibilizar. A coluna \"Prioridade\" segue a classificação MoSCoW (Essencial, Importante, Desejável), utilizada para orientar o planejamento das sprints (Capítulo 3)."),
  tabelaRF,
  new Paragraph({ spacing: { after: 300 }, children: [] }),

  bodyPara("Os requisitos RF01 a RF05 entraram como Essenciais porque, sem eles, não há fluxo funcional: é preciso treinar o modelo, classificar transações em tempo real e permitir que um analista revise os alertas manualmente. RF06 e RF07 ficaram como Importantes — agregam valor real (transparência sobre o desempenho do modelo, capacidade de investigação), mas o sistema continuaria funcionando sem eles se faltasse tempo de desenvolvimento. Nenhum requisito do escopo oficial ficou como Desejável, já que o catálogo de temas do professor orientador definiu um escopo enxuto desde o início; essa categoria fica reservada para funcionalidades que surgirem ao longo do desenvolvimento, como recursos extras do painel visual."),
];

// ---------- CAPÍTULOS PENDENTES ----------
function pendente(titulo, dataEntrega) {
  return [
    h1(titulo),
    bodyPara(`A DESENVOLVER — entrega prevista: ${dataEntrega}.`),
  ];
}

const cap3 = pendente("3 Metodologia Ágil e Gestão do Projeto", "16/09/2026");
const cap4 = pendente("4 Modelagem do Sistema", "27/09/2026 (diagrama de classes) e 03/10/2026 (diagrama de sequência)");
const cap5 = pendente("5 Arquitetura do Sistema", "03/10/2026");
const cap6 = pendente("6 Considerações Finais", "a definir");

// ---------- REFERÊNCIAS ----------
const referencias = [
  h1("Referências"),
  refPara("AGÊNCIA BRASIL. **Com novas regras do BC, registros de fraudes financeiras crescem 10%**. Rio de Janeiro, 2026. Disponível em: https://agenciabrasil.ebc.com.br/economia/noticia/2026-07/com-novas-regras-do-bc-registros-de-fraudes-financeiras-crescem-10. Acesso em: 27 ago. 2026."),
  refPara("BAND. **Fraudes no e-commerce devem superar R$ 8,1 bilhões no Brasil em 2026**. São Paulo, 2026. Disponível em: https://www.band.com.br/economia/noticias/fraudes-no-e-commerce-devem-superar-r-81-bilhoes-no-brasil-em-2026-202608101353. Acesso em: 27 ago. 2026."),
  refPara("METRÓPOLES. **Serasa identificou 743 mil tentativas de golpes on-line no 1º semestre**. Brasília, 2026. Disponível em: https://www.metropoles.com/brasil/serasa-identificou-743-mil-tentativas-de-golpes-on-line-no-1semestre. Acesso em: 27 ago. 2026."),
  refPara("PAGBRASIL. **Tipos de fraude com cartão de crédito em e-commerces**. 2024. Disponível em: https://www.pagbrasil.com/pt-br/blog/fraude/tipos-de-fraude-com-cartao-de-credito-em-e-commerces/. Acesso em: 27 ago. 2026."),
  refPara("SINDICATO DO COMÉRCIO VAREJISTA DE MINAS GERAIS (SINCOMAVI); SERASA EXPERIAN. **Tentativas de fraude batem recorde no primeiro semestre de 2025**. 2025. Disponível em: https://sincomavi.org.br/?p=14584. Acesso em: 27 ago. 2026."),
  new Paragraph({
    spacing: { before: 300, line: LINE_SPACING_15 },
    alignment: AlignmentType.JUSTIFIED,
    children: [new TextRun({
      text: "Observação: as referências acima são majoritariamente fontes jornalísticas/institucionais, adequadas para contextualizar o problema na Introdução. O Referencial Teórico (a desenvolver) deve ser complementado com artigos acadêmicos revisados por pares (Google Scholar, SciELO, IEEE Xplore) sobre detecção de fraude e Machine Learning, além das referências técnicas padrão de Engenharia de Software e Metodologia Científica exigidas pelo template ABNT do ATCC.",
      italics: true, font: FONT, size: SIZE_BODY,
    })],
  }),
];

// ---------- MONTAGEM DO DOCUMENTO ----------
const doc = new Document({
  features: { updateFields: true },
  styles: {
    default: {
      document: { run: { font: FONT, size: SIZE_BODY } },
    },
  },
  sections: [
    {
      properties: { page: { margin: MARGIN } },
      children: capa,
    },
    {
      properties: { page: { margin: MARGIN } },
      children: folhaRosto,
    },
    {
      properties: { page: { margin: MARGIN } },
      children: sumario,
    },
    {
      properties: { page: { margin: MARGIN } },
      headers: {
        default: new Header({
          children: [
            new Paragraph({
              alignment: AlignmentType.RIGHT,
              children: [new TextRun({ children: [PageNumber.CURRENT], font: FONT, size: 20 })],
            }),
          ],
        }),
      },
      children: [
        ...notaAcompanhamento,
        ...cap1,
        ...cap2,
        ...cap3,
        ...cap4,
        ...cap5,
        ...cap6,
        ...referencias,
      ],
    },
  ],
});

Packer.toBuffer(doc).then((buffer) => {
  fs.writeFileSync("Documento_Software.docx", buffer);
  console.log("Documento gerado com sucesso.");
});
