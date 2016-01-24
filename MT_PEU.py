 # -*- coding: utf-8 -*-
"""
Principais classes do motor de cálculo do PEU

@author(es): Daniel, Francisco, Anderson, Victor, Leonardo
@GrupoPesquisa: PROTEC
@LinhadePesquisa: GI-UFBA
"""

# ---------------------------------------------------------------------
# IMPORTAÇÃO DE PACOTES DE TERCEIROS
# ---------------------------------------------------------------------
# Cálculos científicos
from numpy import array, size, linspace, min, max, copy, cos, sin, radians,\
    mean, ones, ndarray, nanmax, nanmin

from numpy.random import uniform, triangular
from scipy.stats import f, t, chi2, norm
from scipy.misc import factorial
from numpy.linalg import inv
from math import floor, log10

# Construção de gráficos
from matplotlib.pyplot import figure, axes, axis, plot, errorbar, xlabel, ylabel,\
    legend, xlim, ylim, close

# Pacotes do sistema operacional
from os import getcwd, sep

# Exception Handling
from warnings import warn

# Sistema
import sys
reload(sys)
sys.setdefaultencoding("utf-8") # Forçar o sistema utilizar o coding utf-8

# ---------------------------------------------------------------------------
# IMPORTAÇÃO DE SUBROTINAS PRÓPRIAS E ADAPTAÇÕES (DESENVOLVIDAS PELO GI-UFBA)
# ---------------------------------------------------------------------------
from PSO.PSO import PSO   # Deve haver uma pasta com os códigos-fonte do PSO
from Grandeza import Grandeza
from subrotinas import Validacao_Diretorio, plot_cov_ellipse, vetor_delta,\
    matriz2vetor, graficos_x_y
from Relatorio import Relatorio
from Flag import flag

class EstimacaoNaoLinear:

    class Fluxo:

        def __init__(self):
            u"""
            Classe voltada para controlar o fluxo de etapas de EstimacaoNaoLinear

            ==========
            ATRIBUTOS:
            ==========

            * Cada atributo representa uma etapa da classe EstimacaoNaoLinear e assumem 2 valores:

                * 0 : o método NÃO foi executado
                * 1 : o método foi executado

            ========
            MÉTODOS:
            ========

            * .SET_ETAPA: método para, na execução da Estimacao, indicar qual etapa está sendo avaliada.o método irá avaliar
            se as etapas predecessoras foram executadas.
            * .reiniciar: reinicia o fluxo. Atribui 0 a todos os atributos.
            * .reiniicarParcial: reiniciar parcialmente o fluxo. Exemplo: quando dados de validação forem inseridos.

            =============
            PROPRIEDADES:
            =============

            * definem as etapas predecessoras e/ou sucessoras de cada etapa (atributo)
            """
            self.gerarEntradas = 0
            self.otimizacao = 0
            self.SETparametro = 0
            self.GETFOotimo = 0
            self.incertezaParametros = 0
            self.regiaoAbrangencia = 0
            self.preencherRegiao = 0
            self.predicao = 0
            self.analiseResiduos = 0
            self.armazenarDicionario = 0
            self.mapeamentoFO = 0
            self.Hessiana = 0
            self.Gy = 0
            self.S = 0

            self.__fluxoID = 0

        def SET_ETAPA(self,etapa,ignoreValidacao=False):
            u"""
            Método voltado para definição de uma etapa e suas validações

            =========
            ENTRADAS:
            =========

            * etapa (string): define a etapa que está sem execução e se deseja validar. Deve ter mesmo nome que um
            dos atributos (em __init__)
            * ignoreValidacao (bool): irá ignorar a validação e atribuir 1 à etapa

            Se o método ocorrer sem erros, atribuirá 1 a etapa.
            """
            if not ignoreValidacao:
                # Teste para verificar se as etapas predecessoras foram executadas
                teste = [getattr(self,elemento) for elemento in getattr(self, '_predecessora_'+etapa)]
                # Caso não haja predecessora, o valor é atribuído a True
                teste = teste if teste != [] else [True]
                # Caso nenhuma predecessora tenha sido executada, retorna um erro
                if not any(teste):
                    raise SyntaxError('Para executar o método {} deve executar antes {}'.format(etapa, ' ou '.join(
                        getattr(self, '_predecessora_' + etapa))))
            # atribuindo o valor 1 (executado) ao atributo referente à etapa, atualmente em execução
            setattr(self, etapa, 1)

        def reiniciar(self,manter='gerarEntradas'):
            u"""
            Método utilizado para reiniciar o fluxo. (IMPACTA todas as etapas)

            Entende-se por reinicialização de fluxo, atribuir o valor de todos os atributos a zero, ou seja,
            como se os métodos de EstimacaoNaoLinear não tivessem sido executados.

            =========
            ENTRADAS:
            =========
            * manter (string): etapa que será mantida como 1.

            =========
            Filosofia
            =========
            * Todas as vezes que dados experimentais são adionados, o fluxo é reiniciado, inclusive definindo que não foram inseridos
             dados de validação
            """
            for atributo in vars(self).keys():
                if atributo != '_Fluxo__fluxo':
                    setattr(self, atributo, 0)

            self.__fluxoID = 0
            setattr(self, manter, 1)

        def reiniciarParcial(self, etapas=None):
            u"""
            Método utilizado para reiniciar apenas etapas específicas

            ========
            ENTRADAS
            ========

            * etapas (list): lista com as etapas que serão reiniciadas.

            =========
            Filosofia
            =========
            * Toda vez que é adicionado dados de validação é iniciado um novo fluxo de trabalho, para que a predição, analise de residuos
             e os respectivos gráficos e relatórios destas etapas sejam corretamente criados.
            """

            etapas = etapas if etapas is not None else self._sucessoresValidacao

            for atributo in etapas:
                setattr(self, atributo, 0)

            self.__fluxoID += 1

        @property
        def FLUXO_ID(self):
            u"""
            Obtém o número de identificação do fluxo
            """

            return self.__fluxoID

        @property
        def _predecessora_gerarEntradas(self):
            return []

        @property
        def _predecessora_otimizacao(self):
            return ['gerarEntradas']

        @property
        def _predecessora_SETparametro(self):
            return []

        @property
        def _predecessora_GETFOotimo(self):
            return ['otimizacao', 'SETparametro']

        @property
        def _predecessora_incertezaParametros(self):
            return ['otimizacao','SETparametro']

        @property
        def _predecessora_regiaoAbrangencia(self):
            return ['mapeamentoFO']

        @property
        def _predecessora_preencherRegiao(self):
            return ['incertezaParametros']

        @property
        def _predecessora_predicao(self):
            # TODO: adequar para a issue #62
            # Prentende-se: ['otimizacao', 'SETparametro']
            return ['incertezaParametros']

        @property
        def _predecessora_analiseResiduos(self):
            return ['predicao']

        @property
        def _predecessora_armazenarDicionario(self):
            return ['gerarEntradas']

        @property
        def _predecessora_mapeamentoFO(self):
            return ['otimizacao','preencherRegiao']

        @property
        def _predecessora_Hessiana(self):
            return ['otimizacao', 'SETparametro']

        @property
        def _predecessora_Gy(self):
            return ['otimizacao', 'SETparametro']

        @property
        def _predecessora_S(self):
            return ['otimizacao', 'SETparametro']

        @property
        def _sucessoresValidacao(self):
            return ['predicao', 'analiseResiduos', 'armazenarDicionario', 'Gy', 'S']

    def __init__(self, FO, Modelo, simbolos_y, simbolos_x, simbolos_param, PA=0.95, projeto='Projeto', **kwargs):
        u"""
        Classe para executar a estimação de parâmetros de modelos não lineares.

        Esta classe conta com um conjunto de métodos para obtenção do ótimo, utilizando a função objetivo WLS
        (weighted least squares), avaliação da incerteza dos parâmetros (com região de abrangência), estimativa da
        predição, cálculo da incerteza da predição e análise de resíduos.

        Classes auxiliares:
        * Grandeza
        * Flag
        * Relatorio

        ======================
        Bibliotecas requeridas
        ======================
        * Numpy
        * Scipy
        * Matplotlib - 1.4.3
        * Math
        * PSO - versão 0.2-beta **Obtida no link https://github.com/ddss/PSO/releases/tag/v0.2-beta. Os códigos devem estar dentro de uma pasta de nome PSO**
        * statsmodels

        =======================
        Entradas (obrigatórias)
        =======================
        * ``FO`` (Thread)           : objeto função objetivo
        * ``Modelo`` (Thread)       : objeto modelo. O modelo deve retornar um array com número de colunas igual ao número de y.
        * ``simbolos_y`` (list)     : lista com os simbolos das variáveis y (Não podem haver caracteres especiais)
        * ``simbolos_x`` (list)     : lista com os simbolos das variáveis x (Não podem haver caracteres especiais)
        * ``simbolos_param`` (list) : lista com o simbolos dos parâmetros   (Não podem haver caracteres especiais)

        ====================
        Entradas (opcionais)
        ====================
        * ``PA`` (float): probabilidade de abrangência da análise. Deve estar entre 0 e 1. Default: 0.95.
        * ``projeto`` (string): nome do projeto (Náo podem haver caracteres especiais)

        ==============================
        Keywords (Entradas opcionais):
        ==============================

        * ``nomes_x``        (list): lista com os nomes para x
        * ``unidades_x``     (list): lista com as unidades para x (inclusive em formato LATEX)
        * ``label_latex_x``  (list): lista com os símbolos das variáveis em formato LATEX

        * ``nomes_y``        (list): lista com os nomes para y
        * ``unidades_y``     (list): lista com as unidades para y (inclusive em formato LATEX)
        * ``label_latex_y``  (list): lista com os símbolos das variáveis em formato LATEX

        * ``nomes_param``       (list): lista com os nomes para os parâmetros (inclusive em formato LATEX)
        * ``unidades_param``    (list): lista com as unidades para os parâmetros (inclusive em formato LATEX)
        * ``label_latex_param`` (list): lista com os símbolos das variáveis em formato LATEX

        * ``base_path`` (string): String que define o diretório pai que serão criados/salvos os arquivos gerados pelo motor de cálculo

        =======
        Métodos
        =======

        Para a realização da estimação de parâmetros de um certo modelo faz-se necessário executar \
        alguns métodos, na ordem indicada (vide observação):

        **ESTIMAÇÂO DE PARÂMETROS**

        * ``gerarEntradas``        : método para incluir dados obtidos de experimentos. Neste há a opção de determinar \
        se estes dados serão utilizados como dados para estimar os parâmetros ou para validação. (Vide documentação do método)
        * ``otimiza``              : método para realizar a otimização, com base nos dados fornecidos em gerarEntradas.
        * ``incertezaParametros``  : método que avalia a incerteza dos parâmetros (Vide documentação do método)
        * ``gerarEntradas``        : (é opcional para inclusão de dados de validação)
        * ``Predicao``             : método que avalia a predição do modelo e sua incerteza ou utilizando os dados de validação. Caso estes \
        não estejam disponíveis, será utilizado os mesmos dados de estimação (Vide documentação do método)
        * ``analiseResiduos``      : método para executar a análise de resíduos (Vide documentação do método)
        * ``graficos``             : método para criação dos gráficos (Vide documentação do método)
        * ``_armazenarDicionario`` : método que returna as grandezas sob a forma de um dicionário (Vide documentação do método)

        **PREDIÇÃO**

        * ``gerarEntradas``        : método para incluir dados obtidos de experimentos. Neste há a opção de determinar \
        se estes dados serão utilizados como dados para estimar os parâmetros ou para validação. (Vide documentação do método)
        * ``SETparametro``         : método adicionar manualmente valores das estimativas dos parâmetros e sua matriz covarãncia. É assumido \
        que os parâmetros foram estimados para o conjunto de dados fornecidos para estimação.
        * ``gerarEntradas``        : (é opcional para inclusão de dados de validação)
        * incertezaParametros      : (é opcional para avaliação da incerteza, caso não incluído em SETparametro). Entretanto, este estará limitado a \
        calcular a matriz de covariância dos parâmetros. Não será avaliada a região de abrangẽncia (esta deve ser incluída via SETparametro)
        * ``Predicao``             : método que avalia a predição do modelo e sua incerteza ou utilizando os dados de validação. Caso estes \
        não estejam disponíveis, será utilizado os mesmos dados de estimação (Vide documentação do método)
        * ``analiseResiduos``      : método para executar a análise de resíduos (Vide documentação do método)
        * ``graficos``             : método para criação dos gráficos (Vide documentação do método)
        * ``_armazenarDicionario`` : método que returna as grandezas sob a forma de um dicionário (Vide documentação do método)


        **OBSERVAÇÃO**: A ordem de execução dos métodos é importante. Esta classe só permite a execução de métodos, caso as etapas predescessoras tenham sido
        executadas. Entretanto, alguns métodos possuem flexibilidade. Segue abaixo algumas exemplos:
        * gerarEntradas para definir os dados de estimação deve ser sempre executado antes de otimiza
        * gerarEntradas para definir os dados de validação deve ser sempre executado antes de predicao
        * graficos é um método que pode ser executado em diferentes momentos:
            * se for solicitado os gráficos das grandezas-entrada, o método pode ser executado logo após gerarEntradas
            * se for solicitado os gráficos da otimização, o método pode ser executado logo após otimização

        =================
        Fluxo de trabalho
        =================

        Esta classe possui uma classe interna, Fluxo, que valida a correta ordem de execução dos métodos. É importante
        salientar que cada vez que o método ``gerarEntradas`` é utilizado, é criado um novo ``Fluxo de trabalho`` ou ele
        ``Reinicia`` todos.

        **Observação 1**: Se forem adicionados diferentes dados de validação (execuções do método gerarEntradas para incluir tais dados), \
        são iniciado novos fluxos.

        **Observação 2**: Se forem adicionados novos dados para estimacao, todo o histórico de fluxos é apagado e reniciado.

        Esta característica permite a avaliação de diferentes dados de valiação consecutivamente (uso dos métodos de Predição, análiseResiduos, graficos),
        após a estimação dos parâmetros (otimiza, incertezaParametros)

        ======
        Saídas
        ======

        As saídas deste motor de cálculo estão, principalmente, sob a forma de atributos e gráficos.
        Os principais atributos de uma variável Estimacao, são:

        * ``x`` : objeto Grandeza que contém todas as informações referentes às grandezas \
        independentes sob a forma de atributos:
            * ``experimental`` : referente aos dados experimentais. Principais atributos: ``matriz_estimativa``, ``matriz_covariancia``
            * ``calculado``    : referente aos dados calculados pelo modelo. Principais atributos: ``matriz_estimativa``, ``matriz_covariancia``
            * ``validacao``    : referente aos dados de validação. Principais atributos: ``matriz_estimativa``, ``matriz_covariancia``
            * ``residuos``     : referente aos resíduos de regressão. Principais atributos: ``matriz_estimativa``, ``estatisticas``

        * ``y``          : objeto Grandeza que contém todas as informações referentes às grandezas \
        dependentes sob a forma de atributos. Os atributos são os mesmos de x.

        * ``parametros`` : objeto Grandeza que contém todas as informações referentes aos parâmetros sob a forma de atributos.
            * ``estimativa``         : estimativa para os parâmetros
            * ``matriz_covariancia`` : matriz de covariância
            * ``matriz_correlacao``   : matriz de correlação
            * ``regiao_abrangencia`` : pontos contidos na região de abrangência

        Obs.: Para informações mais detalhadas, consultar os Atributos da classe Grandeza.

        * ``PA``: probabilidade de abrangência da análise

        ===============
        Função objetivo
        ===============

        A função objetivo deve ser um objeto com uma estrutura específica. Consulte arquivo Funcao_Objetivo.

        OBSERVAÇÃO:
        O Motor de cálculo sempre irá enviar como uma lista argumentos para a função objetivo \
        nesta ordem:

        * vetor com os pontos experimentais das grandezas dependentes
        * matriz com os pontos experimentais das grandezas independentes (cada coluna representa uma grandeza independente)
        * matriz covariância das grandezas dependentes
        * matriz covariância das grandezas independentes
        * argumentos extras a serem passados para o modelo (entrada de usuário)
        * o modelo
        * lista com os símbolos das grandezas independentes
        * lista com os símbolos das grandezas dependentes
        * lista com os símbolos dos parâmetros

        =======
        Modelo
        ======
        O modelo deve ser um objeto com uma estrutura específica. Consulte arquivo Modelo.

        =====================
        Atributos em destaque
        =====================

        CONFIGURAÇÕES:

        * ._configFolder: variável que contém o nome de todas as pastas criadas pelo algoritmo nas etapas de Gráficos e
         relatórios. Alterando o conteúdo de uma chave, altera-se o nomes das pastas. É permitdio alterar o conteúdo das
         chaves (nomes das pastas), mas alterando as chaves ocasionará erros.

        * .__args_user: variável que contém os argumentos extras a serem passados para o modelo. Equivale ao argumento
        args em otimiza.

        * .__flag: classe flag que controla o comportamento do algoritmo. Flags disponíveis:
            *'dadosexperimentais': identifica se dados para a estimação doram inseridos
            * 'dadosvalidacao'   : identifica se dados para validação forma inseridos
            * 'reconciliacao'    : identifica se foi solicitada reconciliação de dados (HOLD: aguarda implementação da
            reconciliação)
            * 'graficootimizacao': identifica se o algoritmo de otimização tem gráficos de desempenho
            * 'relatoriootimizacao': identifica se o algoritmo de otimização possui relatório na forma de um arquivo

        * .__base_path: identifica o caminho raiz nos quais todos gráficos e relatórios serão salvos
        * .__controleFluxo: objeto Fluxo que controla a validação das etapas, e o fluxo de execução do motor de cálculo.
           * .__controleFLuxo.FLUXO_ID: 0 se só houverem dados experimentais. >0 foram inseridos dados de validação (Isto
           é usado na plotagem de gráficos, para evitar que o uso de dados de validação sucessivos sobrescrevam os gráficos)

        OUTROS:

        * .Otimizacao: salva todas as informações do algorimo de otimização. [Só existe após execução do método otimização].
        * ._deltaHessiana: incremento a ser utilizado para avaliar a matriz Hessiana (pode ser definido via kwargs no método
        incertezaParametros e/ou Predicao)
        * ._deltaGy: incremento a ser utilizado para avaliar a matriz Gy (derivadas segundas da função objetivo em relação
        a dados experimentias de y e parâmetros) (pode ser definido via kwargs no método incertezaParametros e/ou Predicao)
        * ._deltaS: incremento a ser utilizado para avalair a transposta da matriz jacobiana do modelo em relação aos
        parâmetros (pode ser definido via kwargs no método incertezaParametros e/ou Predicao)
        * .Hessiana: salva a matriz Hessiana (somente avaliada após incertezaParametros ou Predicao - a depender do método solicitado)
        * .Gy: salva matriz Gy (somente avaliada após incertezaParametros ou Predicao - a depender do método solicitado)
        * .S: salva matriz S (somente avaliada após incertezaParametros ou Predicao - a depender do método solicitado)
        * .estatisticas: dicionário que contém aguns testes estatístcicos (Para outras estatísticas aqui não incluídas
        consulte Grandezas)
        * FOotimo: valor da função objetivo no ponto ótimo
        """
        # ---------------------------------------------------------------------
        # CONTROLE DO FLUXO DE INFORMAÇÕES DO ALGORITMO
        # ---------------------------------------------------------------------
        # FLUXO DE INFORMAÇÕES -> conjunto de etapas do algoritmo
        self.__controleFluxo = self.Fluxo()

        # ---------------------------------------------------------------------
        # VALIDAÇÕES GERAIS DE KEYWORDS
        # ---------------------------------------------------------------------
        # Keywords disponíveis para o método de entrada
        self.__keywordsEntrada = ('nomes_x', 'unidades_x', 'label_latex_x', 'nomes_y', 'unidades_y', 'label_latex_y',
                                  'nomes_param','unidades_param', 'label_latex_param', 'base_path')

        # Validação se houve keywords digitadas incorretamente:
        keyincorreta = [key for key in kwargs.keys() if not key in self.__keywordsEntrada]

        if len(keyincorreta) != 0:
            raise NameError('keyword(s) incorreta(s): ' + ', '.join(keyincorreta) + '.' +
                            ' Keywords disponíveis: ' + ', '.join(self.__keywordsEntrada) + '.')

        # Verificação de PA está entre 0 e 1
        if not 0 < PA < 1:
            raise ValueError('A probabilidade de abrangência deve estar entre 0 e 1.')

        # Verificação se o nome do projeto é um string
        if not isinstance(projeto, str):
            raise TypeError('O nome do projeto deve ser um string.')

        # Verificação se o nome do projeto possui caracteres especiais
        # set: conjunto de elementos distintos não ordenados (trabalha com teoria de conjuntos)
        if set('[~!@#$%^&*()+{}":;\']+$').intersection(projeto):
            raise NameError('O nome do projeto não pode conter caracteres especiais')

        # Verificação se o base_path é uma string
        if kwargs.get(self.__keywordsEntrada[9]) is not None and not isinstance(kwargs.get(self.__keywordsEntrada[9]),
                                                                                  str):
            raise TypeError('A keyword {} deve ser um string.'.format(self.__keywordsEntrada[9]))

        # ---------------------------------------------------------------------
        # INICIALIZAÇÃO DAS GRANDEZAS
        # ---------------------------------------------------------------------
        # Variável      = Grandeza(simbolos      ,nomes                                ,unidades                             ,label_latex                          )
        self.x          = Grandeza(simbolos_x    ,kwargs.get(self.__keywordsEntrada[0]),kwargs.get(self.__keywordsEntrada[1]),kwargs.get(self.__keywordsEntrada[2]))
        self.y          = Grandeza(simbolos_y    ,kwargs.get(self.__keywordsEntrada[3]),kwargs.get(self.__keywordsEntrada[4]),kwargs.get(self.__keywordsEntrada[5]))
        self.parametros = Grandeza(simbolos_param,kwargs.get(self.__keywordsEntrada[6]),kwargs.get(self.__keywordsEntrada[7]),kwargs.get(self.__keywordsEntrada[8]))

        # Verificação se os símbolos são distintos
        # set: conjunto de elementos distintos não ordenados (trabalha com teoria de conjuntos)
        if len(set(self.y.simbolos).intersection(self.x.simbolos)) != 0 or len(set(self.y.simbolos).intersection(self.parametros.simbolos)) != 0 or len(set(self.x.simbolos).intersection(self.parametros.simbolos)) != 0:
            raise NameError('Os símbolos das grandezas devem ser diferentes.')

        # ---------------------------------------------------------------------
        # OUTRAS VARIÁVEIS
        # ---------------------------------------------------------------------
        # Propabilidade de abrangência
        self.PA = PA

        # Incremento das derivadas numéricas
        self._deltaHessiana = 1e-5  # Hessiana da função objetivo
        self._deltaGy = 1e-5        # Gy (derivada parcial segunda da função objetivo em relação aos parâmetros e dados experimentais)
        self._deltaS = 1e-5         # S (transposto do jacobiano do modelo)

        # ---------------------------------------------------------------------
        # CRIAÇÃO DAS VARIÁVEIS INTERNAS
        # ---------------------------------------------------------------------
        # Função objetivo
        self.__FO        = FO
        # Modelo
        self.__modelo    = Modelo
        # Argumentos extras a serem passados para o modelo definidos pelo usuário.
        self.__args_user = None # Aqui iniciado para que possa existir na herança
        # Histórico das posições (parâmetros) do algoritmo de otimização (usado em otimiza e/ou preencher
        #  regiao e/ou regiaoAbrangencia)
        self.__hist_Posicoes = []
        # Histórico do fitness (valor funcao objetivo) do algoritmo de otimização (usado em otimiza e/ou preencher
        #  regiao e/ou regiaoAbrangencia)
        self.__hist_Fitness = []
        # Caminho base para os arquivos, caso seja definido a keyword base_path ela será utilizada.
        if kwargs.get(self.__keywordsEntrada[9]) is None:
            self.__base_path = getcwd()+ sep +str(projeto)+sep
        else:
            self.__base_path = kwargs.get(self.__keywordsEntrada[9])

        # Flags para controle de informações
        self.__flag = flag()
        self.__flag.setCaracteristica(['dadosexperimentais','dadosvalidacao',
                                       'reconciliacao','preenchimentoRegiao',
                                       'graficootimizacao','relatoriootimizacao'])
        # uso das caracterśiticas:
        # dadosexperimentais: indicar se dadosexperimentais foram inseridos
        # dadosvalidacao: indicar se dadosvalidacao foram inseridos
        # reconciliacao: indicar se reconciliacao está sendo executada
        # graficootimizacao: indicar se na etapa de otimização são utilizados algoritmos de otimização que possuem
        #                    gráficos de desempenho
        # relatoriootimizacao: indicar se o algoritmo de otimização possui relatório

        # Variável que controla o nome das pastas criadas pelos métodos gráficos e relatórios
        self._configFolder = {'graficos':'Graficos',
                              'graficos-grandezas-entrada-experimental':'Grandezas',
                              'graficos-grandezas-entrada-validacao':'Grandezas',
                              'graficos-grandezas-calculadas':'Grandezas',
                              'graficos-predicao':'Predicao',
                              'graficos-regiaoAbrangencia':'Regiao',
                              'graficos-otimizacao':'Otimizacao',
                              'graficos-analiseResiduos':'Grandezas',
                              'relatorio':'Relatorios'}

        # Tipos de dados disponíveis para entrada de dados
        self.__tiposDisponiveisEntrada = ('experimental', 'validacao')

        # Algoritmos de otimização disponíveis
        self.__AlgoritmosOtimizacao = ('PSO',)

        # métodos para avaliação da incerteza
        self.__metodosIncerteza = ('2InvHessiana', 'Geral', 'SensibilidadeModelo')

        # keywords disponíveis para avaliação das derivadas
        self.__keywordsDerivadas = ('deltaHess', 'deltaGy', 'deltaS', 'delta')

        # tipos de gráficos disponíveis:
        self.__tipoGraficos = ('regiaoAbrangencia', 'grandezas-entrada', 'predicao', 'grandezas-calculadas',
                               'otimizacao', 'analiseResiduos')

        # tipos de algoritmos de preenchimento de região de abrangência disponíveis
        self.__tipoPreenchimento = ('PSO', 'MonteCarlo')

    def _args_FO(self):
        """
        Método que retorna argumentos extras a serem passados para a função objetivo

        :return: lista (list) com argumentos extras
        """
        # ---------------------------------------------------------------------
        # LISTA DE ATRIBUTOS A SEREM INSERIDOS NA FUNÇÃO OBJETIVO
        # ---------------------------------------------------------------------

        return [self.y.experimental.vetor_estimativa, self.x.experimental.matriz_estimativa,
                self.y.experimental.matriz_covariancia, self.x.experimental.matriz_covariancia,
                self.__args_user, self.__modelo,
                self.x.simbolos, self.y.simbolos, self.parametros.simbolos]

    def _args_model(self):
        """
        Método que retorna argumentos extras a serem passados para o modelo

        :return: lista (list) com argumentos extras
        """
        # ---------------------------------------------------------------------
        # LISTA DE ATRIBUTOS A SEREM INSERIDOS NO MODELO
        # ---------------------------------------------------------------------

        return [self.__args_user,self.x.simbolos,self.y.simbolos,self.parametros.simbolos]

    def __validacaoDadosEntrada(self,dados,udados,NV):
        u"""
        Validação dos dados de entrada

        * verificar se os dados e suas incertezas são arrays de 2 dimensões, com o mesmo número de pontos
        * verificar se as colunas dos arrays de entrada tem o mesmo número dos símbolos das variáveis definidas (y, x)
        * verificar se os graus de liberdade são suficientes para realizar a estimação
        """
        if not isinstance(dados,ndarray):
            raise TypeError('Os vetores de dados informando deve ser um array.')

        if not isinstance(udados,ndarray):
            raise TypeError('O vetor contendo a incerteza dos dados informando deve ser um array.')

        if not dados.ndim == 2:
            raise TypeError('A dimensão dos vetores de dados deve ser 2.')

        if not udados.ndim == 2:
            raise TypeError('A dimensão contendo a incerteza dos dados deve ser 2.')

        if dados.shape[1] != NV:
            raise ValueError('O número de variáveis definidas foi {:d}, mas foram inseridos dados para {:d} variáveis.'.format(NV,dados.shape[1]))

        if udados.shape[1] != NV:
            raise ValueError('O número de variáveis definidas foi {:d}, mas foram inseridas incertezas para {:d}.'.format(NV,udados.shape[1]))

        if dados.shape[0] != udados.shape[0]:
            raise ValueError('Os vetores de dados e suas incertezas devem ter o mesmo número de pontos.')

        if udados.shape[0]*self.y.NV-float(self.parametros.NV) <= 0: # Verificar se há graus de liberdade suficiente
            warn('Graus de liberdade insuficientes. O seu conjunto de dados experimentais não é suficiente para estimar os parâmetros!',UserWarning)

    def gerarEntradas(self,x,y,ux,uy,glx=[],gly=[],tipo='experimental',uxy=None):
        u"""
        Método para incluir os dados de entrada da estimação

        =======================
        Entradas (Obrigatórias)
        =======================

        * x         : array com os dados das variáveis independentes na forma de colunas
        * ux        : array com as incertezas das variáveis independentes na forma de colunas
        * y         : array com os dados das variáveis dependentes na forma de colunas
        * uy        : array com as incertezas das variáveis dependentes na forma de colunas
        * glx       : graus de liberdade para as grandezas de entrada
        * gly       : graus de liberdada para as grandezas de saída
        * tipo      : string que define se os dados são experimentais (para estimação) ou de validação.

        **Aviso**:
        * Caso não definidos dados de validação, será assumido os valores experimentais (de estimação)
        * Caso não definido graus de liberdade para as grandezas, será assumido o valor constante de 100
        """
        # ---------------------------------------------------------------------
        # FLUXO
        # ---------------------------------------------------------------------
        self.__controleFluxo.SET_ETAPA('gerarEntradas')
        # ---------------------------------------------------------------------
        # VALIDAÇÃO
        # ---------------------------------------------------------------------
        # validação do tipo
        if not set([tipo]).issubset(self.__tiposDisponiveisEntrada):
            raise ValueError('A(s) entrada(s) ' + ','.join(
                set([tipo]).difference(self.__tiposDisponiveisEntrada)) + ' não estão disponíveis. Usar: ' + ','.join(
                self.__tiposDisponiveisEntrada) + '.')

        # Validação dos dados de entrada x, y, ux e uy
        self.__validacaoDadosEntrada(x, ux, self.x.NV)
        self.__validacaoDadosEntrada(y, uy, self.y.NV)

        # Validação do número de dados experimentais
        if x.shape[0] != y.shape[0]:
            raise ValueError('Foram inseridos {:d} dados para as grandezas dependentes, mas {:d} para as independentes'.format(y.shape[0],x.shape[0]))

        # ---------------------------------------------------------------------
        # EXECUÇÃO
        # ---------------------------------------------------------------------
        # dados experimentais
        if tipo == self.__tiposDisponiveisEntrada[0]:
            self.__flag.ToggleActive('dadosexperimentais')
            # caso o ID do fluxo seja 0, então não há necessidade de reiniciar, caso contrário, reiniciar.
            if self.__controleFluxo.FLUXO_ID != 0:
                self.__controleFluxo.reiniciar()
                if self.__flag.info['dadosvalidacao']:
                    warn('O fluxo foi reiniciado, faz-se necessário incluir novos dados de validação', UserWarning)
            # ---------------------------------------------------------------------
            # ATRIBUIÇÃO A GRANDEZAS
            # ---------------------------------------------------------------------
            # Salvando os dados experimentais nas variáveis.
            try:
                self.x._SETexperimental(estimativa=x,matriz_incerteza=ux,gL=glx)
            except Exception,erro:
                raise RuntimeError('Erro na criação do conjunto experimental de X: {}'.format(erro))

            try:
                self.y._SETexperimental(estimativa=y,matriz_incerteza=uy,gL=gly)
            except Exception, erro:
                raise RuntimeError('Erro na criação do conjunto experimental de Y: {}'.format(erro))

        # dados de validação
        if tipo == self.__tiposDisponiveisEntrada[1]:
            self.__flag.ToggleActive('dadosvalidacao')

            self.__controleFluxo.reiniciarParcial()
            # ---------------------------------------------------------------------
            # ATRIBUIÇÃO A GRANDEZAS
            # ---------------------------------------------------------------------
            # Salvando os dados de validação.
            try:
                self.x._SETvalidacao(estimativa=x,matriz_incerteza=ux,gL=glx)
            except Exception, erro:
                raise RuntimeError('Erro na criação do conjunto validação de X: {}'.format(erro))

            try:
                self.y._SETvalidacao(estimativa=y,matriz_incerteza=uy,gL=gly)
            except Exception, erro:
                raise RuntimeError('Erro na criação do conjunto validação de Y: {}'.format(erro))

        if not self.__flag.info['dadosvalidacao']:
            # Caso gerarEntradas seja executado somente para os dados experimentais,
            # será assumido que estes são os dados de validação, pois todos os cálculos 
            # de predição são realizados para os dados de validação.
            # ---------------------------------------------------------------------
            # ATRIBUIÇÃO A GRANDEZAS
            # ---------------------------------------------------------------------
            # Salvando os dados de validação.
            try:
                self.x._SETvalidacao(estimativa=x,matriz_incerteza=ux,gL=glx)
            except Exception, erro:
                raise RuntimeError('Erro na criação do conjunto validação de X: {}'.format(erro))

            try:
                self.y._SETvalidacao(estimativa=y,matriz_incerteza=uy,gL=gly)
            except Exception, erro:
                raise RuntimeError('Erro na criação do conjuno validação de Y: {}'.format(erro))

    def _armazenarDicionario(self):
        u"""
        Método opcional para armazenar as Grandezas (x,y e parãmetros) na
        forma de um dicionário, cujas chaves são os símbolos.

        ======
        Saídas
        ======

        * grandeza: dicionário cujas chaves são os símbolos das grandezas e respectivos
        conteúdos objetos da classe Grandezas.
        """
        # ---------------------------------------------------------------------
        # FLUXO
        # ---------------------------------------------------------------------
        self.__controleFluxo.SET_ETAPA('armazenarDicionario')

        # ---------------------------------------------------------------------
        # GERANDO O DICIONÁRIO
        # ---------------------------------------------------------------------    

        grandeza = {}

        # GRANDEZAS DEPENDENTES (y)
        for j, simbolo in enumerate(self.y.simbolos):
            grandeza[simbolo] = Grandeza([simbolo],[self.y.nomes[j]],[self.y.unidades[j]],[self.y.label_latex[j]])

            # Salvando os dados experimentais
            if self.__flag.info['dadosexperimentais']:
                # Salvando dados experimentais
                grandeza[simbolo]._SETexperimental(estimativa=self.y.experimental.matriz_estimativa[:,j:j+1],
                                                   matriz_incerteza=self.y.experimental.matriz_incerteza[:,j:j+1],
                                                   gL=self.y.experimental.gL[j])

            # Salvando os dados validação
            if self.__flag.info['dadosvalidacao']:
                # Salvando dados experimentais
                grandeza[simbolo]._SETvalidacao(estimativa=self.y.validacao.matriz_estimativa[:,j:j+1],
                                                matriz_incerteza=self.y.validacao.matriz_incerteza[:,j:j+1],
                                                gL=self.y.validacao.gL[j])

            # Salvando os dados calculados
            if self.__controleFluxo.predicao:
                grandeza[simbolo]._SETcalculado(estimativa=self.y.calculado.matriz_estimativa[:,j:j+1],
                                                matriz_incerteza=self.y.calculado.matriz_incerteza[:,j:j+1],
                                                gL=self.y.calculado.gL[j])

            # Salvando os resíduos
            if self.__controleFluxo.analiseResiduos:
                grandeza[simbolo]._SETresiduos(estimativa=self.y.residuos.matriz_estimativa[:,j:j+1])

        # GRANDEZAS INDEPENDENTES (x)
        for j, simbolo in enumerate(self.x.simbolos):
            grandeza[simbolo] = Grandeza([simbolo],[self.x.nomes[j]],[self.x.unidades[j]],[self.x.label_latex[j]])

            # Salvando dados experimentais
            if self.__flag.info['dadosexperimentais']:
                grandeza[simbolo]._SETexperimental(estimativa=self.x.experimental.matriz_estimativa[:,j:j+1],
                                                   matriz_incerteza=self.x.experimental.matriz_incerteza[:,j:j+1],
                                                   gL=self.x.experimental.gL[j])

            # Salvando dados de validação
            if self.__flag.info['dadosvalidacao']:
                grandeza[simbolo]._SETvalidacao(estimativa=self.x.validacao.matriz_estimativa[:,j:j+1],
                                                matriz_incerteza=self.x.validacao.matriz_incerteza[:,j:j+1],
                                                gL=self.x.validacao.gL[j])

            # Salvando dados calculados
            if self.__controleFluxo.predicao:
                grandeza[simbolo]._SETcalculado(estimativa=self.x.calculado.matriz_estimativa[:,j:j+1],
                                                matriz_incerteza=self.x.calculado.matriz_incerteza[:,j:j+1],
                                                gL=self.x.calculado.gL[j])

            # Salvando os resíduos
            if self.__controleFluxo.analiseResiduos:
                grandeza[simbolo]._SETresiduos(estimativa=self.x.residuos.matriz_estimativa[:,j:j+1])

        # PARÂMETROS
        for j,simbolo in enumerate(self.parametros.simbolos):
            grandeza[simbolo] = Grandeza([simbolo],[self.parametros.nomes[j]],[self.parametros.unidades[j]],[self.parametros.label_latex[j]])
            if self.__controleFluxo.otimizacao or self.__controleFluxo.SETparametro:
                # Salvando as informações dos parâmetros
                if self.parametros.matriz_covariancia is None:
                    grandeza[simbolo]._SETparametro([self.parametros.estimativa[j]],None,None)
                else:
                    grandeza[simbolo]._SETparametro([self.parametros.estimativa[j]],array([self.parametros.matriz_covariancia[j,j]],ndmin=2),None)

        return grandeza


    def otimiza(self,limite_inferior,limite_superior,estimativa_inicial=None,algoritmo='PSO',args=None,**kwargs):
        u"""
        Método para realização da otimização

        =====================
        Métodos predecessores
        =====================

        Faz-se necessário executaro método ``gerarEntradas``, informando os dados experimentais \
        antes de executar a otimização.

        =======================
        Entradas (obrigatórias)
        =======================

        * limite_inferior (list): lista com os limites inferior para os parâmetros. **Usado para o método de PSO**
        * limite_superior (list): lista com os limites inferior para os parâmetros. **Usado para o método de PSO**

        ====================
        Entradas (opcionais)
        ====================

        * estimativa_inicial (list): lista com as estimativas iniciais para os parâmetros. **Usado para outros métodos de otimização**
        * algoritmo (string): string informando o algoritmo de otimização a ser utilizado. Cada algoritmo tem suas próprias keywords
        * args: argumentos extras a serem passados para o modelo

        ===============================
        Keywords (argumentos opcionais)
        ===============================

        algoritmo = PSO

        Para os argumentos extras para o algoritmo de PSO, vide documentação.

        ==========
        Observação
        ==========
        * Toda vez que a otimização é executada toda informação anterior sobre parâmetros é perdida
        """
        # ---------------------------------------------------------------------
        # FLUXO
        # ---------------------------------------------------------------------
        self.__controleFluxo.SET_ETAPA('otimizacao')
        # ---------------------------------------------------------------------
        # VALIDAÇÃO
        # ---------------------------------------------------------------------

        # se não houver dados experimentais -> erro
        if not self.__flag.info['dadosexperimentais']:
            raise SyntaxError('Para executar a otimização, faz-se necessário dados experimentais')

        # se SETparametro não pode ser executado antes de otimiza.
        if self.__controleFluxo.SETparametro:
            raise SyntaxError('O método {} não pode ser executado com {}'.format('otimiza', 'SETparametro'))

        # verificação se o algoritmo é um string
        if not isinstance(algoritmo, str):
            raise TypeError('O nome do algoritmo deve ser uma string.')

        # verificação se o algoritmo está disponível
        if not algoritmo in self.__AlgoritmosOtimizacao:
            raise NameError(
                'A opção {} de algoritmo não está correta. Algoritmos disponíveis: '.format(algoritmo) + ', '.join(
                    self.__AlgoritmosOtimizacao) + '.')

        # validação da estimativa inicial:
        if estimativa_inicial is not None:
            if not isinstance(estimativa_inicial, list) or len(estimativa_inicial) != self.parametros.NV:
                raise TypeError(
                    'A estimativa inicial deve ser uma lista de dimensão do número de parâmetros, definida nos símbolos. Número de parâmetros: {}'.format(
                        self.parametros.NV))

        # ---------------------------------------------------------------------
        # EXECUÇÃO
        # ---------------------------------------------------------------------
        # EstimacaoNaoLinear executa somente estimação SEM reconciliação
        self.__flag.ToggleInactive('reconciliacao')

        # definindo que args são argumentos extras a serem passados para a função objetivo (e, portanto, não sofrem validação)
        self.__args_user = args

        if algoritmo == 'PSO':
            # indica que este algoritmo possui gráficos de desempenho
            self.__flag.ToggleActive('graficootimizacao')
            # indica que esta algoritmo possui relatório de desempenho
            self.__flag.ToggleActive('relatoriootimizacao')
            # O algoritmo de PSO realiza o mapeamentoFO
            self.__controleFluxo.SET_ETAPA('mapeamentoFO')

            # Separação de keywords para os diferentes métodos
            # keywarg para a etapa de busca:
            kwargsbusca = {}
            if kwargs.get('printit') is not None:
                kwargsbusca['printit'] = kwargs.pop('printit')

            kwargs['NP'] = self.parametros.NV
            # ---------------------------------------------------------------------
            # VALIDAÇÃO DO MODELO
            # ---------------------------------------------------------------------            
            # Verificação se o modelo é executável nos limites de busca
            try:
                aux = self.__modelo(limite_superior,self.x.validacao.matriz_estimativa,self._args_model())
                aux.run()
                aux = self.__modelo(limite_inferior,self.x.validacao.matriz_estimativa,self._args_model())
                aux.run()
            except Exception, erro:
                raise SyntaxError(u'Erro no modelo, quando avaliado nos limites de busca definidos. Erro identificado: "{}".'.format(erro))

            # ---------------------------------------------------------------------
            # EXECUÇÃO OTIMIZAÇÃO
            # ---------------------------------------------------------------------
            # OS argumentos extras (kwargs e kwrsbusca) são passados diretamente para o algoritmo
            self.Otimizacao = PSO(limite_superior,limite_inferior,args_model=self._args_FO(),**kwargs)
            self.Otimizacao.Busca(self.__FO,**kwargsbusca)

            # ---------------------------------------------------------------------
            # HISTÓRICO DA OTIMIZAÇÃO
            # ---------------------------------------------------------------------
            for it in xrange(self.Otimizacao.n_historico):
                for ID_particula in xrange(self.Otimizacao.Num_particulas):
                    self.__hist_Posicoes.append(self.Otimizacao.historico_posicoes[it][ID_particula])
                    self.__hist_Fitness.append(self.Otimizacao.historico_fitness[it][ID_particula])

            # ---------------------------------------------------------------------
            # ATRIBUIÇÃO A GRANDEZAS
            # ---------------------------------------------------------------------
            # Atribuindo o valor ótimo dos parâmetros
            # Toda vez que a otimização é executada toda informação anterior sobre parâmetros é perdida
            self.parametros._SETparametro(self.Otimizacao.gbest,None,None,limite_superior=limite_superior,limite_inferior=limite_inferior)

        # ---------------------------------------------------------------------
        # OBTENÇÃO DO PONTO ÓTIMO DA FUNÇÃO OBJETIVO
        # ---------------------------------------------------------------------
        self.__GETFOotimo()


    def __GETFOotimo(self):
        '''
        Método para obtenção do ponto ótimo da função objetivo
        '''
        # ---------------------------------------------------------------------
        # FLUXO
        # ---------------------------------------------------------------------
        self.__controleFluxo.SET_ETAPA('GETFOotimo')

        # ---------------------------------------------------------------------
        # OBTENÇÃO DO PONTO ÓTIMO DA FUNÇÃO OBJETIVO
        # ---------------------------------------------------------------------
        FO = self.__FO(self.parametros.estimativa, self._args_FO())
        FO.run()

        self.FOotimo = FO.result

    def SETparametro(self,estimativa,variancia=None,regiao=None,**kwargs):
        u"""
        Método para atribuir uma estimativa aos parâmetros e, opcionamente, sua matriz de covarância e região de abrangência.
        Substitui o métodos otimiza e, opcionalmente, incertezaParametros.

        Caso seja incluída somente uma estimativa para os parâmetros, o método incertezaParametro deve ser executado.

        ========
        Entradas
        ========

        * estimativa (list)         : estimativa para os parâmetros
        * variancia (array,ndmin=2) : matriz de covariância dos parâmetros
        * regiao (list[list])       : lista contendo listas com os parâmetros que pertencem á região de abrangência

        ===
        USO
        ===
        * Inclusão da estimativa dos parâmetros: irá substituir o método de otimização. Será necessário executar o método incertezaParametros
        * Inclusão da estimativa dos parâmetros e variancia:  irá substituir o método de otimização e uma parte do método de incertezaParametros. Neste caso, não será possível
        executar o método regiaoAbrangencia, devido à não execução da otimização.
        * Inclusão da estimativa dos parâmetros, variancia e regiao:  irá substituir o método de otimização e incertezaParametros

        =================
        Keyword Arguments
        =================
        * limite_superior: limite superior dos parâmetros
        * limtie_inferior: limite_inferior dos parâmetros
        * args           : argumentos extras a serem passados para o modelo

        =========
        ATRIBUTOS
        =========
        O método irá incluir estas informações no atributo parâmetros
        """
        # ---------------------------------------------------------------------
        # FLUXO
        # ---------------------------------------------------------------------
        self.__controleFluxo.SET_ETAPA('SETparametro')
        # ---------------------------------------------------------------------
        # VALIDAÇÃO
        # ---------------------------------------------------------------------
        # Caso não haja dados experimentais -> erro
        if not self.__flag.info['dadosexperimentais']:
            raise SyntaxError('Faz-se necessário adicionar dados experimentais.')

        # SETparametro não pode ser executado em conjunto com otimiza
        if self.__controleFluxo.otimizacao:
            raise SyntaxError('O método SETparametro não pode ser executado com otimizacao.')

        # ---------------------------------------------------------------------
        # ARGUMENTOS EXTRAS A SEREM PASSADOS PARA O MODELO
        # ---------------------------------------------------------------------
        # Obtenção de args_user
        if kwargs.get('args') is not None:
            self.__args_user = kwargs.pop('args')

        # ---------------------------------------------------------------------
        # ATRIBUIÇÃO A GRANDEZAS
        # ---------------------------------------------------------------------     
        # Atribuindo o valores para a estimativa dos parâmetros e sua matriz de 
        # covariância
        self.parametros._SETparametro(estimativa, variancia, regiao,**kwargs)

        # ---------------------------------------------------------------------
        # AVALIAÇÃO DO MODELO
        # ---------------------------------------------------------------------
        # Avaliação do modelo no ponto ótimo informado
        try:
            aux = self.__modelo(self.parametros.estimativa,self.x.validacao.matriz_estimativa,self._args_model())
            aux.run()
        except Exception, erro:
            raise SyntaxError(u'Erro no modelo quando avaliado na estimativa dos parâmetros informada. Erro identificado: "{}"'.format(erro))

        # ---------------------------------------------------------------------
        # OBTENÇÃO DO PONTO ÓTIMO
        # ---------------------------------------------------------------------
        # Só usa o método GETFOotimo se este não fora executado
        if not self.__controleFluxo.GETFOotimo:
            self.__GETFOotimo()

        # ---------------------------------------------------------------------
        # VARIÁVEIS INTERNAS
        # ---------------------------------------------------------------------

        # Caso seja definida a variância, é assumido que o método incertezaParametros
        # foi executado, mesmo que a inclusão de abrangência seja opcional.
        if variancia is not None:
            self.__controleFluxo.SET_ETAPA('incertezaParametros')

        # Caso seja definida a região, é assumido que o método regiaoAbrangencia
        # foi executado.
        if regiao is not None:
            self.__controleFluxo.SET_ETAPA('regiaoAbrangencia', ignoreValidacao=True)

    def incertezaParametros(self,metodoIncerteza='2InvHessiana',preencherregiao=False,**kwargs):
        u"""

        Método para avaliação da matriz de covariãncia dos parâmetros e região de abrangência.

        ===================
        Método predescessor
        ===================

        É necessário executar a otimização ou SETparametro.

        =======================
        Entradas (opcionais)
        =======================

        * metodoIncerteza (string) : método para cálculo da matriz de covariãncia dos
        parâmetros. Métodos disponíveis: 2InvHessiana, Geral, SensibilidadeModelo
        * preencherregiao (bool): identifica de será executado algoritmo para preenchimento da região de abrangência.

        ======
        Saídas
        ======
        * a matriz de covariância dos parâmetros é salva na Grandeza parâmetros

        ==========
        Observação
        ==========
        * A região de abrangência só é executada caso haja histórico da otimização (ETAPA: mapeamentoFO) e o atributo regiao_abrangencia
        de parâmetros não esteja definido.

        ==========================
        Keyword Arguments (kwargs)
        ==========================

        * deltaHess: delta a ser utilizado para a matriz Hessiana
        * deltaGy: delta a ser utilzido para a matriz de derivadas parciais segunda da função objetivo em relação
        aos parâmetros e dados experimentais (y)
        * deltaS: delta a ser utilizado na matriz de derivadas do modelo em relação dos parâmetros.
        * delta: quando definido, ajusta deltaHess, deltaGy e deltaS para o valor definido
        * kwargs para o algoritmo de PSO para executar o preenchimento da região.
        """
        # ---------------------------------------------------------------------
        # FLUXO
        # ---------------------------------------------------------------------
        self.__controleFluxo.SET_ETAPA('incertezaParametros')
        # ---------------------------------------------------------------------
        # VALIDAÇÃO
        # ---------------------------------------------------------------------         

        if metodoIncerteza not in self.__metodosIncerteza:
            raise NameError('O método solicitado para cálculo da incerteza dos parâmetros {}'.format(metodoIncerteza)
                            + ' não está disponível. Métodos disponíveis ' + ', '.join(self.__metodosIncerteza) + '.')

        if not isinstance(preencherregiao, bool):
            raise TypeError('O argumento preencherregião deve ser booleano (True ou False).')

        # ---------------------------------------------------------------------
        # DELTAS (INCREMENTO) DAS DERIVADAS
        # ---------------------------------------------------------------------
        if kwargs.get('delta') is not None:
            kwargs['deltaHess'] = kwargs['delta']
            kwargs['deltaGy']   = kwargs['delta']
            kwargs['deltaS']    = kwargs['delta']
            kwargs.pop('delta')

        self._deltaHessiana = kwargs.pop('deltaHess') if kwargs.get('deltaHess') is not None else self._deltaHessiana
        self._deltaGy = kwargs.pop('deltaGy') if kwargs.get('deltaGy') is not None else self._deltaGy
        self._deltaS = kwargs.pop('deltaS') if kwargs.get('deltaS') is not None else self._deltaS

        # ---------------------------------------------------------------------
        # MATRIZ DE COVARIÂNCIA DOS PARÂMETROS
        # ---------------------------------------------------------------------

        # Avaliação de matrizes auxiliares
        # Matriz Hessiana da função objetivo em relação aos parâmetros
        # somente avaliada se o método é 2InvHess ou Geral
        if metodoIncerteza == self.__metodosIncerteza[0] or metodoIncerteza == self.__metodosIncerteza[1]:
            self.Hessiana   = self.__Hessiana_FO_Param(self._deltaHessiana)

            # Inversa da matriz hessiana a função objetivo em relação aos parâmetros
            invHess = inv(self.Hessiana)

        # Gy: derivadas parciais segundas da função objetivo em relação aos parâmetros e
        # dados experimentais
        # Somente avaliada caso o método seja Geral
        if metodoIncerteza == self.__metodosIncerteza[1]:
            self.Gy  = self.__Matriz_Gy(self._deltaGy)

        # Matriz de sensibilidade do modelo em relação aos parâmetros
        # Somente avaliada caso o método seja o simplificado
        if metodoIncerteza == self.__metodosIncerteza[2]:
            self.S   = self.__Matriz_S(self.x.experimental.matriz_estimativa,self._deltaS)

        # ---------------------------------------------------------------------
        # AVALIAÇÃO DA INCERTEZA DOS PARÂMETROS
        # ---------------------------------------------------------------------

        # MATRIZ DE COVARIÂNCIA
        # Método: 2InvHessiana ->  2*inv(Hess)
        if metodoIncerteza == self.__metodosIncerteza[0]:
            matriz_covariancia = 2*invHess

        # Método: geral - > inv(H)*Gy*Uyy*GyT*inv(H)
        elif metodoIncerteza == self.__metodosIncerteza[1]:
            matriz_covariancia  = invHess.dot(self.Gy).dot(self.y.experimental.matriz_covariancia).dot(self.Gy.transpose()).dot(invHess)

        # Método: simplificado -> inv(trans(S)*inv(Uyy)*S)
        elif metodoIncerteza == self.__metodosIncerteza[2]:
            matriz_covariancia = inv(self.S.transpose().dot(inv(self.y.experimental.matriz_covariancia)).dot(self.S))

        # ---------------------------------------------------------------------
        # ATRIBUIÇÃO A GRANDEZA
        # ---------------------------------------------------------------------
        self.parametros._updateParametro(matriz_covariancia=matriz_covariancia)

        # ---------------------------------------------------------------------
        # REGIÃO DE ABRANGÊNCIA
        # ---------------------------------------------------------------------
        # PREENCHIMENTO DE REGIÃO:
        if preencherregiao and self.parametros.NV != 1:
            self.__preencherRegiao(**kwargs)
            self.__flag.ToggleActive('preenchimentoRegiao')

        # A região de abrangência só é executada caso haja histórico de posicoes e fitness
        if self.__controleFluxo.mapeamentoFO and self.parametros.NV != 1:
            # OBTENÇÃO DA REGIÃO:
            regiao = self.regiaoAbrangencia()
            # ATRIBUIÇÃO A GRANDEZA
            self.parametros._updateParametro(regiao_abrangencia=regiao)

    def predicao(self,**kwargs):
        u"""
        Método para realizar a predição.

        ====================
        Método predecessores
        ====================

        É necessário executar a otimização (seguida de incertezaParametros) ou incluir o valor para a estimativa dos parâmetros e sua incerteza, pelo \
        método ``SETparametro`` (caso não defina incerteza, executar em seguida de incertezaParametros).


        =================
        Keyword arguments
        =================
        ** Por default, este método vai utilizar os últimos deltas definidos na etapa de avaliação da incerteza **

        * deltaHess: delta a ser utilizado para a matriz Hessiana
        * deltaGy: delta a ser utilzido para a matriz de derivadas parciais da função objetivo em relação
        aos parâmetros e dados experimentais
        * deltaS: delta a ser utilizado na matriz de derivadas do modelo em relação dos parâmetros.
        * delta: quando definido, ajusta deltaHess, deltaGy e deltaS para o valor definido.
        """
        # ---------------------------------------------------------------------
        # FLUXO
        # ---------------------------------------------------------------------
        self.__controleFluxo.SET_ETAPA('predicao')

        # ---------------------------------------------------------------------
        # VALIDAÇÃO
        # ---------------------------------------------------------------------      
        keyincorreta = [key for key in kwargs.keys() if not key in self.__keywordsDerivadas]

        if len(keyincorreta) != 0:
            raise NameError('keyword(s) incorreta(s): ' + ', '.join(keyincorreta) + '.' +
                            ' Keywords disponíveis: ' + ', '.join(self.__keywordsDerivadas) + '.')

        # ---------------------------------------------------------------------
        # DELTAS (INCREMENTO) DAS DERIVADAS
        # ---------------------------------------------------------------------
        if kwargs.get('delta') is not None:
            kwargs['deltaHess'] = kwargs['delta']
            kwargs['deltaGy'] = kwargs['delta']
            kwargs['deltaS'] = kwargs['delta']

        self._deltaHessiana = kwargs.get('deltaHess') if kwargs.get('deltaHess') is not None else self._deltaHessiana
        self._deltaGy = kwargs.get('deltaGy') if kwargs.get('deltaGy') is not None else self._deltaGy
        self._deltaS = kwargs.get('deltaS') if kwargs.get('deltaS') is not None else self._deltaS

        # ---------------------------------------------------------------------
        # AVALIAÇÃO DAS MATRIZES AUXILIARES
        # ---------------------------------------------------------------------

        # Matriz Hessiana da função objetivo em relação aos parâmetros
        # Somente reavaliada caso o método que a avalia não tenha sido executado E não tenha dados validacao
        if not self.__controleFluxo.Hessiana and not self.__flag.info['dadosvalidacao']:
            self.Hessiana = self.__Hessiana_FO_Param(self._deltaHessiana)

        # Inversa da matriz hessiana a função objetivo em relação aos parâmetros
        # Só avaliada se o método de avaliação da Hessiana for executado E não tenha dados validacao
        if self.__controleFluxo.Hessiana:
            invHess = inv(self.Hessiana)

        # Gy: derivadas parciais segundas da função objetivo em relação aos parâmetros e 
        # dados experimentais
        # Somente reavaliada caso o método que a avalia não tenha sido executado E não tenha dados validacao
        if not self.__controleFluxo.Gy and not self.__flag.info['dadosvalidacao']:
            self.Gy  = self.__Matriz_Gy(self._deltaGy)

        # S: transposto do jacobiano do modelo em relação aos parâmetros
        # Somente reavaliada caso não tenha sido avaliada OU se tenha dados de validação
        if not self.__controleFluxo.S or self.__flag.info['dadosvalidacao']:
            # Matriz de sensibilidade do modelo em relação aos parâmetros
            self.S   = self.__Matriz_S(self.x.validacao.matriz_estimativa,self._deltaS)

        # ---------------------------------------------------------------------
        # PREDIÇÃO
        # ---------------------------------------------------------------------
        aux = self.__modelo(self.parametros.estimativa,self.x.validacao.matriz_estimativa,self._args_model())
        aux.run()

        # ---------------------------------------------------------------------
        # AVALIAÇÃO DA PREDIÇÃO (Y CALCULADO PELO MODELO)
        # ---------------------------------------------------------------------    
        # MATRIZ DE COVARIÃNCIA DE Y
        # Se os dados de validação forem diferentes dos experimentais, será desconsiderado
        # a covariância entre os parâmetros e dados experimentais
        if self.__flag.info['dadosvalidacao']:

            Uyycalculado = self.S.dot(self.parametros.matriz_covariancia).dot(self.S.transpose()) + self.y.validacao.matriz_covariancia

        else:
            # Neste caso, os dados de validação são os dados experimentais e será considerada
            # a covariância entre os parâmetros e dados experimentais
            # COVARIÃNCIA ENTRE PARÂMETROS E DADOS EXPERIMENTAIS
            Covar_param_y_experimental = -invHess.dot(self.Gy).dot(self.y.validacao.matriz_covariancia)
            # PRIMEIRA PARCELA
            Uyycalculado_1 = self.S.dot(self.parametros.matriz_covariancia).dot(self.S.transpose())
            # SEGUNDA PARCELA            
            Uyycalculado_2 = self.S.dot(Covar_param_y_experimental)
            # TERCEIRA PARCELA
            Uyycalculado_3 = Covar_param_y_experimental.transpose().dot(self.S.transpose())
            # MATRIZ DE COVARIÃNCIA DE Y
            Uyycalculado   = Uyycalculado_1 + Uyycalculado_2 + Uyycalculado_3 + self.y.experimental.matriz_covariancia

        # --------------------------------------------------------------------
        # ATRIBUIÇÃO A GRANDEZAS
        # -------------------------------------------------------------------
        self.y._SETcalculado(estimativa=aux.result,matriz_covariancia=Uyycalculado,
                             gL=[[self.y.experimental.NE*self.y.NV-self.parametros.NV]*self.y.validacao.NE]*self.y.NV,
                             NE=self.y.validacao.NE)
        self.x._SETcalculado(estimativa=self.x.validacao.matriz_estimativa,matriz_covariancia=self.x.validacao.matriz_covariancia,
                             gL=[[self.x.experimental.NE*self.x.NV-self.parametros.NV]*self.x.validacao.NE]*self.x.NV,
                             NE=self.x.validacao.NE)

    def __Hessiana_FO_Param(self,delta=1e-5):
        u"""
        Método para calcular a matriz Hessiana da função objetivo em relaçao aos parâmetros.

        Está disponível o método de derivada central de segunda ordem.

        ========
        Entradas
        ========
        * delta(float): valor do incremento relativo para o cálculo da derivada. Incremento relativo à ordem de grandeza do parâmetro.

        =====
        Saída
        =====

        Retorna a matriz Hessiana(array)

        ==========
        Referência
        ==========
        """
        # ---------------------------------------------------------------------
        # FLUXO
        # ---------------------------------------------------------------------
        self.__controleFluxo.SET_ETAPA('Hessiana')
        #---------------------------------------------------------------------------------------
        # DEFINIÇÃO DA MATRIZ DE DERIVADAS PARCIAIS DA FUNÇÃO OBJETIVO EM RELAÇÃO AOS PARÂMETROS
        #----------------------------------------------------------------------------------------

        #Criação de matriz de ones com dimenção:(número de parâmetrosXnúmero de parâmetros) a\
        #qual terá seus elementos substituidos pelo resultado da derivada das  funçâo em relação aos\
        #parâmetros i e j de acordo determinação do for.
        matriz_hessiana=[[1. for col in range(self.parametros.NV)] for row in range(self.parametros.NV)]

        # Valor da função objetivo nos argumentos determinados pela otmização, ou seja, valor no ponto ótimo.
        FO_otimo = self.FOotimo

        #Estrutura iterativa para deslocamento pela matriz Hessiana anteriormente definida.
        for i in range(self.parametros.NV):
            for j in range(self.parametros.NV):

                # Incrementos para as derivadas dos parâmetros, tendo delta1 e delta2 aplicados a qual parãmetro está ocorrendo a alteração\
                #no vetor de parâmetros que é argumento da FO.
                # Obs.: SE O VALOR DO PARÂMETRO FOR ZERO, APLICA-SE OS VALORES DE ''delta'' para ''delta1'' e/ou ''delta2'', pois não existe log de zero, causando erro.

                delta1 = (10**(floor(log10(abs(self.parametros.estimativa[i])))))*delta if self.parametros.estimativa[i] != 0 else delta
                delta2 = (10**(floor(log10(abs(self.parametros.estimativa[j])))))*delta if self.parametros.estimativa[j] != 0 else delta

                #---------------------------------------------------------------------------------------
                # Aplicação da derivada numérica de segunda ordem para os elementos da diagonal principal.
                #----------------------------------------------------------------------------------------

                if i==j:

                    # Vetor com o incremento no parâmetro i
                    vetor_parametro_delta_positivo = vetor_delta(self.parametros.estimativa,i,delta1)
                    # Vetor com o incremento no parâmetro j.
                    vetor_parametro_delta_negativo = vetor_delta(self.parametros.estimativa,j,-delta2)

                    # Cálculo da função objetivo para seu respectivo vetor alterado para utilização na derivação numérica.
                    # Inicialização das threads
                    FO_delta_positivo=self.__FO(vetor_parametro_delta_positivo,self._args_FO())
                    FO_delta_positivo.start()
                    FO_delta_positivo.join()

                    FO_delta_negativo=self.__FO(vetor_parametro_delta_negativo,self._args_FO())
                    FO_delta_negativo.start()
                    FO_delta_negativo.join()

                    # Fórmula de diferença finita para i=j. (Disponível em, Gilat, Amos; MATLAB Com Aplicação em Engenharia, 2a ed, Bookman, 2006.)
                    matriz_hessiana[i][j]=(FO_delta_positivo.result-2*FO_otimo+FO_delta_negativo.result)/(delta1*delta2)

                #-------------------------------------------------------------------------------
                #Aplicação da derivada numérica de segunda ordem para os demais elementos da matriz.
                #-----------------------------------------------------------------------------------
                else:
                    # vetor com o incremento do parâmetro i,j
                    vetor_parametro_delta_ipositivo_jpositivo = vetor_delta(self.parametros.estimativa,[i,j],[delta1,delta2])

                    FO_ipositivo_jpositivo=self.__FO(vetor_parametro_delta_ipositivo_jpositivo,self._args_FO())
                    FO_ipositivo_jpositivo.start()
                    FO_ipositivo_jpositivo.join()

                    vetor_parametro_delta_inegativo_jpositivo=vetor_delta(self.parametros.estimativa,[i,j],[-delta1,delta2])

                    FO_inegativo_jpositivo=self.__FO(vetor_parametro_delta_inegativo_jpositivo,self._args_FO())
                    FO_inegativo_jpositivo.start()
                    FO_inegativo_jpositivo.join()

                    vetor_parametro_delta_ipositivo_jnegativo=vetor_delta(self.parametros.estimativa,[i,j],[delta1,-delta2])

                    FO_ipositivo_jnegativo=self.__FO(vetor_parametro_delta_ipositivo_jnegativo,self._args_FO())
                    FO_ipositivo_jnegativo.start()
                    FO_ipositivo_jnegativo.join()

                    vetor_parametro_delta_inegativo_jnegativo=vetor_delta(self.parametros.estimativa,[i,j],[-delta1,-delta2])

                    FO_inegativo_jnegativo=self.__FO(vetor_parametro_delta_inegativo_jnegativo,self._args_FO())
                    FO_inegativo_jnegativo.start()
                    FO_inegativo_jnegativo.join()

                    # Fórmula de diferença finita para i=~j. Dedução do próprio autor, baseado em intruções da bibliografia:\
                    #(Gilat, Amos; MATLAB Com Aplicação em Engenharia, 2a ed, Bookman, 2006.)
                    matriz_hessiana[i][j]=((FO_ipositivo_jpositivo.result-FO_inegativo_jpositivo.result)/(2*delta1)\
                    -(FO_ipositivo_jnegativo.result-FO_inegativo_jnegativo.result)/(2*delta1))/(2*delta2)

        return array(matriz_hessiana)

    def __Matriz_Gy(self,delta=1e-5):
        u"""
        Método para calcular a matriz Gy(derivada segunda da Fobj em relação aos parâmetros e y_experimentais).

        Método de derivada central dada na forma parcial, em relação as variáveis\
        dependentes distintas.

        ========
        Entradas
        ========

        * delta(float): valor do incremento relativo para o cálculo da derivada.\
        Incremento relativo à ordem de grandeza do parâmetro ou da variável dependente.

        =====
        Saída
        =====
        * return a matriz Gy(array).

        ==========
        Referência
        ==========
        """
        # ---------------------------------------------------------------------
        # FLUXO
        # ---------------------------------------------------------------------
        self.__controleFluxo.SET_ETAPA('Gy')

        # ---------------------------------------------------------------------
        # EXECUÇÃO
        # ---------------------------------------------------------------------
        #Criação de matriz de ones com dimenção:(número de var. independentes* NE X número de parâmetros) a\
        #qual terá seus elementos substituidos pelo resultado da derivada das  funçâo em relação aos\
        #parâmetros i e Ys j de acordo determinação do for.

        matriz_Gy = [[1. for col in xrange(self.y.NV*self.y.experimental.NE)] for row in xrange(self.parametros.NV)]

        #Estrutura iterativa para deslocamento pela matriz Gy anteriormente definida.
        for i in xrange(self.parametros.NV):
            for j in xrange(self.y.NV*self.y.experimental.NE):

                # Incremento no vetor de parâetros
                # --------------------------------------------------------------
                # OBS.: SE O VALOR DO PARÂMETRO e/ou DO Y FOR ZERO, APLICA-SE OS VALORES DE ''delta'' para ''delta1'' e/ou ''delta2'', pois não existe log de zero, causando erro.
                # --------------------------------------------------------------
                delta1 = (10**(floor(log10(abs(self.parametros.estimativa[i])))))*delta           if self.parametros.estimativa[i]           != 0 else delta
                # incremento para a derivada nos valores de y
                delta2 = (10**(floor(log10(abs(self.y.experimental.vetor_estimativa[j])))))*delta if self.y.experimental.vetor_estimativa[j] != 0 else delta

                #Vetor alterado dos parâmetros para entrada na função objetivo
                vetor_parametro_delta_ipositivo = vetor_delta(self.parametros.estimativa,i,delta1)
                vetor_y_delta_jpositivo         = vetor_delta(self.y.experimental.vetor_estimativa,j,delta2)

                # Agumentos extras a serem passados para a FO.
                args                            = copy(self._args_FO()).tolist()
                # Posição [0] da lista de argumantos contem o vetor das variáveis dependentes que será alterado.
                args[0]                         = vetor_y_delta_jpositivo

                FO_ipositivo_jpositivo          = self.__FO(vetor_parametro_delta_ipositivo,args) # Valor da _FO para vetores de Ys e parametros alterados.
                FO_ipositivo_jpositivo.start()
                FO_ipositivo_jpositivo.join()

                # Processo similar ao anterior. Uso de subrrotina vetor_delta.
                vetor_parametro_delta_inegativo = vetor_delta(self.parametros.estimativa,i,-delta1)

                FO_inegativo_jpositivo          = self.__FO(vetor_parametro_delta_inegativo,args) # Valor da _FO para vetores de Ys e parametros alterados.
                FO_inegativo_jpositivo.start()
                FO_inegativo_jpositivo.join()

                vetor_y_delta_jnegativo         = vetor_delta(self.y.experimental.vetor_estimativa,j,-delta2)
                args                            = copy(self._args_FO()).tolist()
                args[0]                         = vetor_y_delta_jnegativo

                FO_ipositivo_jnegativo          = self.__FO(vetor_parametro_delta_ipositivo,args) #Mesma ideia, fazendo isso para aplicar a equação de derivada central de segunda ordem.
                FO_ipositivo_jnegativo.start()
                FO_ipositivo_jnegativo.join()

                FO_inegativo_jnegativo          = self.__FO(vetor_parametro_delta_inegativo,args) #Idem
                FO_inegativo_jnegativo.start()
                FO_inegativo_jnegativo.join()

                # Fórmula de diferença finita para i=~j. Dedução do próprio autor, baseado em intruções da bibliografia:\
                # (Gilat, Amos; MATLAB Com Aplicação em Engenharia, 2a ed, Bookman, 2006.)
                matriz_Gy[i][j]=((FO_ipositivo_jpositivo.result-FO_inegativo_jpositivo.result)/(2*delta1)\
                -(FO_ipositivo_jnegativo.result-FO_inegativo_jnegativo.result)/(2*delta1))/(2*delta2)

        return array(matriz_Gy)

    def __Matriz_Sx(self,delta=1e-5):
        u"""
        Método para calcular a matriz Sx(derivadas primeiras da função do modelo em relação as grandezas de entrada x).

        Método de derivada central de primeira ordem em relação aos parâmetros(considera os parâmetros como variáveis do modelo).

        ========
        Entradas
        ========

        * delta(float): valor do incremento relativo para o cálculo da derivada. Incremento relativo à ordem de grandeza do parâmetro.

        =====
        Saída
        =====

        Retorna a matriz Sx(array).
        """
        pass

    def __Matriz_S(self,x,delta=1e-5):
        u"""
        Método para calcular a matriz S(derivadas primeiras da função do modelo em relação aos parâmetros).

        Método de derivada central de primeira ordem em relação aos parâmetros(considera os parâmetros como variáveis do modelo).

        ========
        Entradas
        ========
        * x (array): vetor contendo a matriz das estimativas das grandezas independentes
        * delta(float): valor do incremento relativo para o cálculo da derivada. Incremento relativo à ordem de grandeza do parâmetro.

        =====
        Saída
        =====

        Retorna a matriz S(array).
        """
        # ---------------------------------------------------------------------
        # FLUXO
        # ---------------------------------------------------------------------
        self.__controleFluxo.SET_ETAPA('S')
        # ---------------------------------------------------------------------
        # EXECUÇÃO
        # ---------------------------------------------------------------------
        #Criação de matriz de ones com dimenção:(número de Y*NE X número de parâmetros) a\
        #qual terá seus elementos substituidos pelo resultado da derivada das  função em relação aos\
        #parâmetros i de acordo o seguinte ''for''.

        matriz_S = ones((self.y.NV*self.y.validacao.NE,self.parametros.NV))

        for i in xrange(self.parametros.NV):

                # Incrementos para as derivadas dos parâmetros, tendo delta_alpha aplicados a qual parâmetro está ocorrendo a alteração\
                #no vetor de parâmetros que é argumento da FO.

                #--------------------------------------------------------------
                #OBS.: SE O VALOR DO PARÂMETRO FOR ZERO, APLICA-SE OS VALORES DE ''delta'' para delta_alpha, pois não existe log de zero, causando erro.
                #--------------------------------------------------------------
                delta_alpha = (10**(floor(log10(abs(self.parametros.estimativa[i])))))*delta if self.parametros.estimativa[i] != 0 else delta

                #Vetores alterados dos parâmetros para entrada na função do modelo
                vetor_parametro_delta_i_positivo = vetor_delta(self.parametros.estimativa,i,delta_alpha)
                vetor_parametro_delta_i_negativo = vetor_delta(self.parametros.estimativa,i,-delta_alpha)

                #Valores para o modelo com os parâmetros acrescidos (matriz na foma de array).
                ycalculado_delta_positivo       = self.__modelo(vetor_parametro_delta_i_positivo,x,self._args_model())

                ycalculado_delta_positivo.start()
                ycalculado_delta_positivo.join()

                #Valores para o modelo com os parâmetros decrescidos (matriz na foma de array).
                ycalculado_delta_negativo       = self.__modelo(vetor_parametro_delta_i_negativo,x,self._args_model())

                ycalculado_delta_negativo.start()
                ycalculado_delta_negativo.join()

                # Fórmula de diferença finita de primeira ordem. Fonte bibliográfica bibliográfia:\
                #(Gilat, Amos; MATLAB Com Aplicação em Engenharia, 2a ed, Bookman, 2006.) - página (?)
                matriz_S[:,i:i+1] =  (matriz2vetor(ycalculado_delta_positivo.result) - matriz2vetor(ycalculado_delta_negativo.result))/(2*delta_alpha)

        return matriz_S

    def __preencherRegiao(self,**kwargs):
        u"""
        Método utilizado para preenchimento da região de abrangência

        =================
        Keyword arguments
        =================
            * metodoPreenchimento ('string'): define qual o método utilizado no preenchimento da região de abrangência. Se: PSO ou MonteCarlo (
         Monte Carlo)
        PSO:
            * argumentos extras a serem passados para o PSO (Vide documentação do método)
        MonteCarlo:
            * limite_superior (list): limite máximo que define a região de abrangência.
            * limite_inferior (list): limite mínimo que define a região de abrangência.
            * iteracoes (int): número de iterações a serem realizadas. Default: 10000.
            * fatorlimitebusca: quanto maior este fator, maior a faixa automática de busca baseada no range que a elipse abrange. Default: 1/10
            * distribuicao (string): define como as amostras de parâmetros são geradas. Default: uniforme (até 2 parâmetros), triangular (mais de 3 parâmetros)
        """
        # ---------------------------------------------------------------------
        # FLUXO
        # ---------------------------------------------------------------------
        self.__controleFluxo.SET_ETAPA('preencherRegiao')
        self.__controleFluxo.SET_ETAPA('mapeamentoFO')

        # ---------------------------------------------------------------------
        # VALIDAÇÃO
        # ---------------------------------------------------------------------
        tipo = kwargs.get('metodoPreenchimento') if kwargs.get('metodoPreenchimento') is not None else 'MonteCarlo'

        # avaliando se o tipo de preenchimento está disponível
        if tipo not in self.__tipoPreenchimento:
            raise NameError('O método solicitado para preenchimento da região de abrangência {}'.format(
                tipo) + ' não está disponível. Métodos disponíveis ' + ', '.join(self.__tipoPreenchimento) + '.')

        # caso seja MonteCarlo:
        if tipo == self.__tipoPreenchimento[1]:
            kwargsdisponiveis = ('iteracoes', 'limite_superior', 'limite_inferior', 'metodoPreenchimento',
                                 'fatorlimitebusca','distribuicao')

            # avaliando se as keywords estão disponíveis
            if not set(kwargs.keys()).issubset(kwargsdisponiveis):
                raise NameError('O(s) keyword(s) argument digitado(s) está(ão) incorreto(s). Keyword disponíveis: ' +
                                ', '.join(kwargsdisponiveis) + '.')
            # avaliando o número de iterações -> dever ser maior do que 1
            if kwargs.get(kwargsdisponiveis[0]) is not None:
                if kwargs.get(kwargsdisponiveis[0]) < 1:
                    raise ValueError('O número de iterações deve ser inteiro e positivo.')
            # avaliando o fatorlimite -> deve ser positivo
            if kwargs.get(kwargsdisponiveis[4]) is not None:
                if kwargs.get(kwargsdisponiveis[4]) < 0:
                    raise ValueError('O fator limite busca deve positivo.')
            # avaliando a distribuição
            if kwargs.get(kwargsdisponiveis[5]) is not None:
                if kwargs.get(kwargsdisponiveis[5]) not in ['uniforme', 'triangular']:
                    raise ValueError('As distribuições disponíveis para o Método de MonteCarlo são: {}.'.format(['uniforme', 'triangular']))

        # ---------------------------------------------------------------------
        # LIMTES DE BUSCA
        # ---------------------------------------------------------------------
        limite_superior = kwargs.get('limite_superior')
        limite_inferior = kwargs.get('limite_inferior')
        fatorlimitebusca =  kwargs.get('fatorlimitebusca') if kwargs.get('fatorlimitebusca') is not None else 1/10.

        if limite_superior is None or limite_inferior is None:
            extremo_elipse_superior = [0 for i in xrange(self.parametros.NV)]
            extremo_elipse_inferior = [0 for i in xrange(self.parametros.NV)]

            fisher, FOcomparacao = self.__criteriosAbrangencia()

            Combinacoes = int(factorial(self.parametros.NV) / (factorial(self.parametros.NV - 2) * factorial(2)))
            p1 = 0
            p2 = 1
            cont = 0
            passo = 1

            for pos in xrange(Combinacoes):
                if pos == (self.parametros.NV - 1) + cont:
                    p1 += 1
                    p2 = p1 + 1
                    passo += 1
                    cont += self.parametros.NV - passo

                cov = array([[self.parametros.matriz_covariancia[p1, p1], self.parametros.matriz_covariancia[p1, p2]],
                             [self.parametros.matriz_covariancia[p2, p1], self.parametros.matriz_covariancia[p2, p2]]])

                ellipse, coordenadas_x, coordenadas_y = plot_cov_ellipse(cov, [self.parametros.estimativa[p1], self.parametros.estimativa[p2]],
                                                                     FOcomparacao)

                extremo_elipse_superior[p1] = nanmax(coordenadas_x)
                extremo_elipse_superior[p2] = nanmax(coordenadas_y)
                extremo_elipse_inferior[p1] = nanmin(coordenadas_x)
                extremo_elipse_inferior[p2] = nanmin(coordenadas_y)
                p2+=1

        if limite_superior is None:
            limite_superior = [extremo_elipse_superior[i] + (extremo_elipse_superior[i]-extremo_elipse_inferior[i])*fatorlimitebusca for i in xrange(self.parametros.NV)]
        else:
            kwargs.pop('limite_superior') # retira limite_superior dos argumentos extras

        if limite_inferior is None:
            limite_inferior = [extremo_elipse_inferior[i] - (extremo_elipse_superior[i]-extremo_elipse_inferior[i])*fatorlimitebusca for i in xrange(self.parametros.NV)]
        else:
            kwargs.pop('limite_inferior') # retira limite_inferior dos argumentos extras

        # ---------------------------------------------------------------------
        # MÉTODO DO PSO
        # ---------------------------------------------------------------------
        if tipo == self.__tipoPreenchimento[0]:

            if kwargs.get('itmax') is None:
                kwargs['itmax'] = 500

            if kwargs.get('metodo') is None:
                kwargs['metodo'] = {'busca':'Regiao','algoritmo':'PSO','inercia':'Constante'}
                kwargs['otimo']  = self.parametros.estimativa

            # Separação de keywords para os diferentes métodos
            # keywarg para a etapa de busca:
            kwargsbusca = {}
            if kwargs.get('printit') is not None:
                kwargsbusca['printit'] = kwargs.get('printit')
                del kwargs['printit']

            kwargs['NP'] = self.parametros.NV

            PSO_preenchimento = PSO(limite_superior,limite_inferior,args_model=self._args_FO(),**kwargs)
            PSO_preenchimento.Busca(self.__FO,**kwargsbusca)

            # ---------------------------------------------------------------------
            # HISTÓRICO DA OTIMIZAÇÃO
            # ---------------------------------------------------------------------
            for it in xrange(PSO_preenchimento.n_historico):
                for ID_particula in xrange(PSO_preenchimento.Num_particulas):
                    self.__hist_Posicoes.append(PSO_preenchimento.historico_posicoes[it][ID_particula])
                    self.__hist_Fitness.append(PSO_preenchimento.historico_fitness[it][ID_particula])

        # ---------------------------------------------------------------------
        # MÉTODO MONTE CARLO
        # ---------------------------------------------------------------------
        if tipo == self.__tipoPreenchimento[1]:
            iteracoes = int(kwargs.get('iteracoes') if kwargs.get('iteracoes') is not None else 10000)
            distribuicao = kwargs.get('distribuicao')
            if distribuicao is None:
                if self.parametros.NV <= 2:
                    distribuicao = 'uniforme'
                else:
                    distribuicao = 'triangular'

            for cont in xrange(iteracoes):
                if distribuicao == 'uniforme':
                    amostra = [uniform(limite_inferior[i], limite_superior[i], 1)[0]
                               for i in xrange(self.parametros.NV)]
                else:
                    amostra = [triangular(limite_inferior[i], self.parametros.estimativa[i], limite_superior[i], 1)[0]
                               for i in xrange(self.parametros.NV)]

                FO = self.__FO(amostra, self._args_FO())
                FO.run()
                self.__hist_Posicoes.append(amostra)
                self.__hist_Fitness.append(FO.result)

    def __criteriosAbrangencia(self):
        u"""
        Método que retorna os valores das distribuições de Fisher, chi2 e o valor limite da função objetivo.
        Utilizado para avaliar a região de abrangẽncia
        """

        # TesteF = F(PA,NP,NE*NY-NP)
        fisher = f.ppf(self.PA,self.parametros.NV,(self.y.experimental.NE*self.y.NV-self.parametros.NV))

        # Valor máximo da função objetivo que um certo conjunto de parâmetros pode gerar para estar contido
        # na região de abrangência
        FOcomparacao = self.FOotimo*(1+float(self.parametros.NV)/(self.y.experimental.NE*self.y.NV-float(self.parametros.NV))*fisher)

        return fisher, FOcomparacao

    def regiaoAbrangencia(self):
        u"""
        Método para avaliação da região de abrangência pelo critério de Fisher, conhecidas
        como região de verossimilhança [1].

        ==========
        Referência
        ==========
        [1] SCHWAAB, M. et al. Nonlinear parameter estimation through particle swarm optimization. Chemical Engineering Science, v. 63, n. 6, p. 1542–1552, mar. 2008.
        """
        # ---------------------------------------------------------------------
        # FLUXO
        # ---------------------------------------------------------------------
        self.__controleFluxo.SET_ETAPA('regiaoAbrangencia')

        # ---------------------------------------------------------------------
        # DETERMINAÇÃO DA REGIÃO DE ABRANGÊNCIA PELO CRITÉRIO DE FISHER
        # ---------------------------------------------------------------------
        fisher, FOcomparacao = self.__criteriosAbrangencia()

        # Comparação dos valores da função objetivo avaliados na etapa de otimização com FOcomparacao, caso
        # sejam menores, os respectivos parâmetros estarão contidos da região de abrangência.
        regiao = []
        for pos,fitness in enumerate(self.__hist_Fitness):
            if fitness <= FOcomparacao+self.FOotimo:
                regiao.append(self.__hist_Posicoes[pos])

        # ---------------------------------------------------------------------
        # AVALIAÇÃO SE A REGIÃO DE ABRANGÊNCIA NÃO ESTÁ VAZIA (Warning)
        # ---------------------------------------------------------------------
        if regiao == []:
            warn('A região de abrangência avaliada pelo método da verossimilhança não contém pontos. Reveja os parâmetros do algoritmo utilizado.',UserWarning)

        return regiao

    def analiseResiduos(self):
        u"""
        Método para realização da análise de resíduos.
        A análise da sempre preferência aos dados de validação.

        ======
        Saídas
        ======
        * Cálculo do R2 e R2 ajustado (atributos: R2 e R2ajustado)
        * Aplicação de testes estatísticos para as grandezas. Criação do atributo estatisticas para cada grandeza x e y. (Vide documentação de Grandeza)
        * Teste estatítico para avaliar se a função objetivo segue uma chi2 (atributo estatisticas)
              * Se FO pertence ao intervalo chi2min < FO < chi2max, tem uma situação ideal, então o modelo representa bem os dados

               Caso contrário há duas situações possíveis ao se analisar a FO com a chi2:

              * FO < chi2min, O modelo representa os dados esperimentais muito melhor que o esperado,
              o que pode indicar que há super parametrização do modelo ou que os erros esperimentais estão superestimados:
              * FO > chi2max: o modelo não é capaz de explicar os erros experimentais
              ou pode haver subestimação dos erros esperimentais
        """
        # ---------------------------------------------------------------------
        # FLUXO
        # ---------------------------------------------------------------------
        self.__controleFluxo.SET_ETAPA('analiseResiduos')
        # ---------------------------------------------------------------------
        # VALIDAÇÃO
        # ---------------------------------------------------------------------         

        # Tamanho dos vetores:
        if self.y.validacao.NE != self.y.calculado.NE:
            raise TypeError(u'O comprimento dos vetores de validação e calculado não estão consistentes. Avaliar necessidade de executar o método de predição')
        # ---------------------------------------------------------------------
        # CÁLCULO DOS RESÍDUOS
        # ---------------------------------------------------------------------          
        # Calculos dos residuos (ou desvios) - estão baseados nos dados de validação
        residuo_y = self.y.validacao.matriz_estimativa - self.y.calculado.matriz_estimativa
        residuo_x = self.x.validacao.matriz_estimativa - self.x.calculado.matriz_estimativa

        # ---------------------------------------------------------------------
        # ATRIBUIÇÃO A GRANDEZAS
        # ---------------------------------------------------------------------       
        # Attribuição dos valores nos objetos
        self.x._SETresiduos(estimativa=residuo_x)
        self.y._SETresiduos(estimativa=residuo_y)

        # ---------------------------------------------------------------------
        # CÁLCULO DE R2 e R2 ajustado
        # ---------------------------------------------------------------------   
        self.estatisticas = {'R2': {}, 'R2ajustado': {}, 'FuncaoObjetivo': {}}
        # Para y:
        for i,symb in enumerate(self.y.simbolos):
            SSE = sum(self.y.residuos.matriz_estimativa[:,i]**2)
            SST = sum((self.y.validacao.matriz_estimativa[:,i]-\
                  mean(self.y.validacao.matriz_estimativa[:,i]))**2)
            self.estatisticas['R2'][symb]         = 1 - SSE/SST
            self.estatisticas['R2ajustado'][symb] = 1 - (SSE/(self.y.validacao.NE-self.parametros.NV))\
                                       /(SST/(self.y.validacao.NE - 1))
        # Para x:                                           
        for i,symb in enumerate(self.x.simbolos):
            if self.__flag.info['reconciliacao']:
                SSEx = sum(self.x.residuos.matriz_estimativa[:,i]**2)
                SSTx = sum((self.x.validacao.matriz_estimativa[:,i]-\
                      mean(self.x.validacao.matriz_estimativa[:,i]))**2)
                self.estatisticas['R2'][symb]         = 1 - SSEx/SSTx
                self.estatisticas['R2ajustado'][symb] = 1 - (SSEx/(self.x.validacao.NE-self.parametros.NV))\
                                           /(SSTx/(self.x.validacao.NE - 1))
            else:
                self.estatisticas['R2'][symb]         = None
                self.estatisticas['R2ajustado'][symb] = None

        # ---------------------------------------------------------------------
        # EXECUÇÃO DE TESTES ESTATÍSTICOS
        # ---------------------------------------------------------------------             
        # Grandezas independentes
        if self.__flag.info['reconciliacao']:
            self.x._testesEstatisticos(self.y.experimental.matriz_estimativa)

        # Grandezas dependentes            
        self.y._testesEstatisticos(self.x.experimental.matriz_estimativa)

        # ---------------------------------------------------------------------
        # VALIDAÇÃO DO VALOR DA FUNÇÃO OBJETIVO COMO UMA CHI 2
        # ---------------------------------------------------------------------
        # TODO: substituir pelo grau de liberdade dos parâmetros, após merge com INcertezaParametros
        gL = self.y.experimental.NE*self.y.NV - self.parametros.NV

        chi2max = chi2.ppf(self.PA+(1-self.PA)/2,gL)
        chi2min = chi2.ppf((1-self.PA)/2,gL)

        self.estatisticas['FuncaoObjetivo'] = {'chi2max':chi2max,'chi2min':chi2min,'FO':self.FOotimo}

    def graficos(self,tipos):
        u"""
        Métodos para gerar e salvar os gráficos

        =======================
        Entradas (obrigatórias)
        =======================
        * ``tipos`` (list): lista contendo strings referentes aos tipos de gráficos que se deseja criar
            * 'regiaoAbrangencia': gráficos da região de abrangência dos parâmetros
            * 'grandezas-entrada': gráficos referentes aos dados de entrada e de validação
            * 'predicao': gráficos da predição
            * 'grandezas-calculadas': gráficos dos valores calculados de cada grandeza
            * 'otimizacao': gráficos referentes à otimização (depende do algoritmo utilizado)
            * 'analiseResiduos': gráficos referentes à análise de resíduos.
        """

        # ---------------------------------------------------------------------
        # VALIDAÇÃO
        # ---------------------------------------------------------------------         
        # validando se os tipos de gráficos
        if not isinstance(tipos, list):
            raise TypeError('Os tipos de gráficos devem ser definidos em uma lista.')
        # validando se os tipos de gráficos foram corretamente definidos
        if not set(tipos).issubset(self.__tipoGraficos):
            raise NameError('O(s) tipo(s) de gráfico(s) selecionado(s) não está(ão) disponível(is): ' + ', '.join(
                set(tipos).difference(self.__tipoGraficos)) + '. Tipos disponíveis: ' + ', '.join(
                self.__tipoGraficos) + '.')

        # ---------------------------------------------------------------------
        # CAMINHO BASE
        # ---------------------------------------------------------------------         
        base_path = self.__base_path + sep + self._configFolder['graficos'] + sep

        # ---------------------------------------------------------------------
        # GRÁFICOS
        # --------------------------------------------------------------------- 
        # Gráficos referentes aos dados de entrada (experimentais)
        # grandezas-entrada
        if (self.__tipoGraficos[1] in tipos):
            # se gerarEntradas foi executado alguma vez:
            if self.__controleFluxo.gerarEntradas:
                base_dir = sep + self._configFolder['graficos-grandezas-entrada-experimental'] + sep
                Validacao_Diretorio(base_path,base_dir)
                # gráficos gerados para os dados experimentais
                if self.__flag.info['dadosexperimentais'] == True:
                    self.x.Graficos(base_path, base_dir, ID=['experimental'], fluxo=0)
                    self.y.Graficos(base_path, base_dir, ID=['experimental'], fluxo=0)

                    # Gráficos das grandezas y em função de x
                    for iy in xrange(self.y.NV):
                        for ix in xrange(self.x.NV):
                            graficos_x_y(self.x, self.y, ix, iy, base_path, base_dir, 'experimental',0)

                # gráficos gerados para os dados de validação, apenas se estes forem diferentes dos experimentais,
                # apesar dos atributos de validação sempre existirem
                if self.__flag.info['dadosvalidacao'] == True:
                    base_dir = sep + self._configFolder['graficos-grandezas-entrada-validacao'] + sep
                    Validacao_Diretorio(base_path, base_dir)
                    self.x.Graficos(base_path, base_dir, ID=['validacao'], fluxo=self.__controleFluxo.FLUXO_ID)
                    self.y.Graficos(base_path, base_dir, ID=['validacao'], fluxo=self.__controleFluxo.FLUXO_ID)

                    # Gráficos das grandezas y em função de x
                    for iy in xrange(self.y.NV):
                        for ix in xrange(self.x.NV):
                            graficos_x_y(self.x, self.y, ix, iy, base_path, base_dir, 'validacao',self.__controleFluxo.FLUXO_ID)
            else:
                warn('Os gráficos de entrada não puderam ser criados, pois o método gerarEntradas não foi executado.',UserWarning)

        # Gráficos referentes aos dados de saída (calculados)
        # grandezas-calculado
        if self.__tipoGraficos[3] in tipos:
            base_dir = sep + self._configFolder['graficos-grandezas-calculadas'] + sep
            Validacao_Diretorio(base_path, base_dir)

            # a incerteza dos parâmetros foi alguma vez executada
            if self.__controleFluxo.incertezaParametros:
                self.parametros.Graficos(base_path, base_dir, ID=['parametro'], fluxo=self.__controleFluxo.FLUXO_ID)
            else:
                warn('Os gráficos envolvendo somente as grandezas calculadas (PARÂMETROS) não puderam ser criados, pois o método incertezaParametros não foi executado.',UserWarning)

            # Predição deve ter sido executada no fluxo de trabalho
            if self.__controleFluxo.predicao:
                self.x.Graficos(base_path, base_dir, ID=['calculado'], fluxo=self.__controleFluxo.FLUXO_ID)
                self.y.Graficos(base_path, base_dir, ID=['calculado'], fluxo=self.__controleFluxo.FLUXO_ID)

            else:
                warn('Os gráficos envolvendo somente as grandezas calculadas (X e Y) não puderam ser criados, pois o método predicao não foi executado.',UserWarning)
        # otimização
        if self.__tipoGraficos[4] in tipos:
            base_dir = sep + self._configFolder['graficos-otimizacao'] + sep
            Validacao_Diretorio(base_path, base_dir)
            # otimiza deve ter sido alguma vez no contexto global e o algoritmo de otimização possui gráficos de desempenho
            if self.__controleFluxo.otimizacao and self.__flag.info['graficootimizacao']:
                # Gráficos da otimização
                self.Otimizacao.Graficos(base_path+base_dir,Nome_param=self.parametros.labelGraficos(),FO2a2=True)

            else:
                warn('Os gráficos de otimizacao não puderam ser criados, o algoritmo de otimização utilizado não possui gráficos de desempenho OU o método otimizacao não foi executado.',UserWarning)

        # regiaoAbrangencia
        if self.__tipoGraficos[0] in tipos:
            # os gráficos da região de abrangência só são executados se a matriz de covariância
            # dos parâmetros existir.
            if self.parametros.matriz_covariancia is not None:
                # Gráficos da estimação
                base_dir = sep + self._configFolder['graficos-regiaoAbrangencia'] + sep
                Validacao_Diretorio(base_path, base_dir)
                # os gráficos só podem ser executado se o número de parâmetros for
                # maior do que 1
                if self.parametros.NV != 1:
                    # numéro de combinações não repetidas para os parâmetros
                    Combinacoes = int(factorial(self.parametros.NV)/(factorial(self.parametros.NV-2)*factorial(2)))
                    p1 = 0; p2 = 1; cont = 0; passo = 1 # inicialiação dos contadores (pi e p2 são indinces dos parâmetros
                    # passp: contabiliza o número de parâmetros avaliados
                    # cont: contador que contabiliza (param.NV - passo1)+(param.NV - passo2)

                    for pos in xrange(Combinacoes):
                        if pos == (self.parametros.NV-1)+cont:
                            p1 +=1; p2 = p1+1; passo +=1
                            cont += self.parametros.NV-passo

                        fig = figure()
                        ax = fig.add_subplot(1,1,1)

                        # PLOT de região de abrangência pelo método da verossimilhança
                        if self.__controleFluxo.regiaoAbrangencia:
                            aux1 = [] # lista auxiliar -> região de abrangência para o parâmetro p1
                            aux2 = [] # lista auxiliar -> região de abrangência para o parâmetro p1
                            for it in xrange(size(self.parametros.regiao_abrangencia)/self.parametros.NV):
                                aux1.append(self.parametros.regiao_abrangencia[it][p1])
                                aux2.append(self.parametros.regiao_abrangencia[it][p2])
                            verossimilhanca, = plot(aux1,aux2,'bo',linewidth=2.0,zorder=1)

                        # PLOT da região de abrangência pelo método da linearização (elipse)
                        fisher, FOcomparacao = self.__criteriosAbrangencia()

                        cov = array([[self.parametros.matriz_covariancia[p1,p1],self.parametros.matriz_covariancia[p1,p2]],
                                     [self.parametros.matriz_covariancia[p2,p1],self.parametros.matriz_covariancia[p2,p2]]])
                        ellipse, coordenadas_x, coordenadas_y = plot_cov_ellipse(cov,
                                                                [self.parametros.estimativa[p1],self.parametros.estimativa[p2]],
                                                                FOcomparacao, fill=False, color='r', linewidth=2.0, zorder=2, ax=ax)
                        # PLOT do ponto ótimo
                        plot(self.parametros.estimativa[p1],self.parametros.estimativa[p2],'r*',markersize=10.0,zorder=2)
                        # PLOT dos pontos extremos da elipse (correção da escala)
                        plot(coordenadas_x,coordenadas_y,'.r',markersize=0.01)

                        if self.__controleFluxo.regiaoAbrangencia and self.parametros.regiao_abrangencia != []:
                            legend([ellipse,verossimilhanca],['Elipse',u'Verossimilhança'],loc='best', fontsize=15)
                        elif self.__controleFluxo.regiaoAbrangencia and self.parametros.regiao_abrangencia == []:
                            legend([ellipse],['Ellipse'],loc='best', fontsize=15)

                        # LEGENDA
                        ax.set_xlabel(self.parametros.labelGraficos()[p1], fontsize=20)
                        ax.set_ylabel(self.parametros.labelGraficos()[p2], fontsize=20)
                        # GRID
                        ax.yaxis.grid(color='gray', linestyle='dashed')
                        ax.xaxis.grid(color='gray', linestyle='dashed')
                        # FORMATO DOS EIXOS
                        ax.yaxis.get_major_formatter().set_powerlimits((0, 1))
                        ax.xaxis.get_major_formatter().set_powerlimits((0, 1))
                        # TICKS e NÚMEROS
                        ax.get_xaxis().tick_bottom() # tick no fundo
                        ax.get_yaxis().tick_left()   # tick no esquerda
                        ax.get_yaxis().set_tick_params(direction='out', labelsize=14)
                        ax.get_xaxis().set_tick_params(direction='out', labelsize=14)
                        # MODIFCANDO A ÁREA DE PLOTAGEM
                        fig.subplots_adjust(left=0.12, right=0.95, top=0.94, bottom=0.12)
                        # SALVA O GRÁFICO
                        fig.savefig(base_path+base_dir+'regiao_verossimilhanca_fl'+str(0)+'_'+
                                    str(self.parametros.simbolos[p1])+'_'+str(self.parametros.simbolos[p2])+'.png')
                        close()
                        p2+=1
                else:
                    warn('Os gráficos de regiao de abrangencia não puderam ser criados, pois há apenas um parâmetro.',UserWarning)

            else:
                warn('Os gráficos de regiao de abrangência não puderam ser criados, pois o método incertezaParametros não foi executado OU no método SETparametros não foi definida a variância dos parâmetros',UserWarning)
        # predição
        if self.__tipoGraficos[2] in tipos:
            # Predição deve ter sido executada neste fluxo
            if self.__controleFluxo.predicao:
                base_dir = sep + self._configFolder['graficos-predicao'] + sep
                Validacao_Diretorio(base_path,base_dir)
                #gráficos de y em função de y
                for iy in xrange(self.y.NV):
                    for ix in xrange(self.x.NV):
                        graficos_x_y(self.x, self.y, ix, iy, base_path, base_dir, 'calculado', self.__controleFluxo.FLUXO_ID)

                #incerteza_expandida_Yc=ones((self.y.calculado.NE,self.y.NV))
                #incerteza_expandida_Ye=ones((self.y.validacao.NE,self.y.NV))

                t_cal=t.ppf((1-self.PA)/2, self.y.calculado.gL[0][0])
                t_val=t.ppf((1-self.PA)/2, self.y.validacao.gL[0][0])

                for iy in xrange(self.y.NV):
                        # Gráfico comparativo entre valores experimentais e calculados pelo modelo, sem variância
                        y  = self.y.validacao.matriz_estimativa[:,iy]
                        ym = self.y.calculado.matriz_estimativa[:,iy]
                        diagonal = linspace(min(y),max(y))

                        fig = figure()
                        ax = fig.add_subplot(1,1,1)
                        plot(y,ym,'bo',linewidth=2.0)
                        plot(diagonal,diagonal,'k-',linewidth=2.0)
                        ax.yaxis.grid(color='gray', linestyle='dashed')
                        ax.xaxis.grid(color='gray', linestyle='dashed')
                        label_tick_x   = ax.get_xticks().tolist()
                        tamanho_tick_x = (label_tick_x[1] - label_tick_x[0])/2
                        ymin   = min(ym) - tamanho_tick_x
                        ymax   = max(ym) + tamanho_tick_x
                        xlim((ymin,ymax))
                        ylim((ymin,ymax))

                        if self.__flag.info['dadosvalidacao'] == True:
                            xlabel(self.y.labelGraficos('validacao')[iy])
                        else:
                            xlabel(self.y.labelGraficos('experimental')[iy])

                        ylabel(self.y.labelGraficos('calculado')[iy])

                        if self.__flag.info['dadosvalidacao'] == True:
                            fig.savefig(base_path+base_dir+'grafico_fl'+str(self.__controleFluxo.FLUXO_ID)+'_'+str(self.y.simbolos[iy])+'val_vs_'+str(self.y.simbolos[iy])+'calc_sem_var.png')
                        else:
                            fig.savefig(base_path+base_dir+'grafico_fl'+str(self.__controleFluxo.FLUXO_ID)+'_'+str(self.y.simbolos[iy])+'exp_vs_'+str(self.y.simbolos[iy])+'calc_sem_var.png')
                        close()

                        yerr_calculado=-t_cal*self.y.calculado.matriz_incerteza[:,iy]

                        yerr_experimental=-t_val*self.y.validacao.matriz_incerteza[:,iy]

                        # Gráfico comparativo entre valores experimentais e calculados pelo modelo, com variância
                        #yerr_calculado    = incerteza_expandida_Yc[:,iy]
                        #yerr_experimental = incerteza_expandida_Ye[:,iy]

                        fig = figure()
                        errorbar(y,ym,xerr=yerr_experimental,yerr=yerr_calculado,fmt="none", marker='o',color='b',linestyle='None')
                        plot(diagonal,diagonal,'k-',linewidth=2.0)

                        ax.yaxis.grid(color='gray', linestyle='dashed')
                        ax.xaxis.grid(color='gray', linestyle='dashed')

                        label_tick_y   = ax.get_yticks().tolist()
                        tamanho_tick_y = (label_tick_y[1] - label_tick_y[0])/2

                        ymin   = min(ym - yerr_calculado) - tamanho_tick_y
                        ymax   = max(ym + yerr_calculado) + tamanho_tick_y

                        xlim((ymin,ymax))
                        ylim((ymin,ymax))

                        if self.__flag.info['dadosvalidacao'] == True:
                            xlabel(self.y.labelGraficos('validacao')[iy])
                        else:
                            xlabel(self.y.labelGraficos('experimental')[iy])

                        ylabel(self.y.labelGraficos('calculado')[iy])

                        if self.__flag.info['dadosvalidacao'] == True:
                            fig.savefig(base_path+base_dir+'grafico_fl'+str(self.__controleFluxo.FLUXO_ID)+'_'+str(self.y.simbolos[iy])+'val_vs_'+str(self.y.simbolos[iy])+'calc_com_var.png')
                        else:
                            fig.savefig(base_path+base_dir+'grafico_fl'+str(self.__controleFluxo.FLUXO_ID)+'_'+str(self.y.simbolos[iy])+'exp_vs_'+str(self.y.simbolos[iy])+'calc_com_var.png')
                        close()

                        if not self.__flag.info['dadosvalidacao']:

                            ycalc_inferior_F = []
                            ycalc_superior_F = []
                            for iNE in xrange(self.y.calculado.NE):

                                ycalc_inferior_F.append(self.y.calculado.matriz_estimativa[iNE,iy]+\
                                            t_val\
                                            *(f.ppf((self.PA+(1-self.PA)/2),self.y.calculado.gL[iy][iNE],\
                                            self.y.validacao.gL[iy][iNE])*self.y.validacao.matriz_covariancia[iNE,iNE])**0.5)

                                ycalc_superior_F.append(self.y.calculado.matriz_estimativa[iNE,iy]-t_val\
                                               *(f.ppf((self.PA+(1-self.PA)/2),self.y.calculado.gL[iy][iNE],\
                                            self.y.validacao.gL[iy][iNE])*self.y.validacao.matriz_covariancia[iNE,iNE])**0.5)

                            fig = figure()
                            ax = fig.add_subplot(1,1,1)
                            errorbar(y,ym,xerr=yerr_experimental,yerr=yerr_calculado,fmt="none",marker='o',color='b',linestyle='None')
                            plot(diagonal,diagonal,'k-',linewidth=2.0)
                            plot(y,ycalc_inferior_F,color='red')
                            plot(y,ycalc_superior_F,color='k')

                            ax.yaxis.grid(color='gray', linestyle='dashed')
                            ax.xaxis.grid(color='gray', linestyle='dashed')
                            label_tick_y   = ax.get_yticks().tolist()
                            tamanho_tick_y = (label_tick_y[1] - label_tick_y[0])/2

                            ymin   = min(ym - yerr_calculado) - tamanho_tick_y
                            ymax   = max(ym + yerr_calculado) + tamanho_tick_y

                            xlim((ymin,ymax))
                            ylim((ymin,ymax))

                            if self.__flag.info['dadosvalidacao']:
                                xlabel(self.y.labelGraficos('validacao')[iy])
                            else:
                                xlabel(self.y.labelGraficos('experimental')[iy])

                            ylabel(self.y.labelGraficos('calculado')[iy])

                            if self.__flag.info['dadosvalidacao'] == True:
                                fig.savefig(base_path+base_dir+'grafico_fl'+str(self.__controleFluxo.FLUXO_ID)+'_'+str(self.y.simbolos[iy])+'val_vs_'+str(self.y.simbolos[iy])+'calc_teste_F.png')
                            else:
                                fig.savefig(base_path+base_dir+'grafico_fl'+str(self.__controleFluxo.FLUXO_ID)+'_'+str(self.y.simbolos[iy])+'exp_vs_'+str(self.y.simbolos[iy])+'calc_teste_F.png')
                            close()

            else:
                warn('Os gráficos envolvendo a estimação (predição) não puderam ser criados, pois o método predicao não foi executado.',UserWarning)

        # AnáliseResiduos
        if (self.__tipoGraficos[5] in tipos):
            # o método análise de resíduos deve ter sido executado
            if self.__controleFluxo.analiseResiduos:
                base_dir = sep + self._configFolder['graficos-analiseResiduos'] + sep
                Validacao_Diretorio(base_path,base_dir)
                # Gráficos relacionados aos resíduos das grandezas independentes, caso
                # seja realizada a reconciliação
                if self.__flag.info['reconciliacao'] == True:
                    self.x.Graficos(base_path, base_dir, ID=['residuo'], fluxo=self.__controleFluxo.FLUXO_ID)

                # Gráficos relacionados aos resíduos das grandezas dependentes
                self.y.Graficos(base_path, base_dir, ID=['residuo'], fluxo=self.__controleFluxo.FLUXO_ID)

                # Grafico dos resíduos em função dos dados de validação (ou experimentais) e calculados
                for i,simb in enumerate(self.y.simbolos):
                    base_dir = sep + self._configFolder['graficos-analiseResiduos'] + sep + self.y.simbolos[i] + sep
                    Validacao_Diretorio(base_path,base_dir)
                    #ymodelo vs. Resíduos
                    fig = figure()
                    ax = fig.add_subplot(1,1,1)
                    plot(self.y.calculado.matriz_estimativa[:,i],self.y.residuos.matriz_estimativa[:,i], 'o')
                    plot([min(self.y.calculado.matriz_estimativa[:,i]),max(self.y.calculado.matriz_estimativa[:,i])],[mean(self.y.residuos.matriz_estimativa[:,i])]*2, '-.r', label=u'Média resíduos '+self.y.simbolos[i])
                    xlabel(u'Valores calculados '+self.y.labelGraficos()[i])
                    ylabel(u'Resíduos '+self.y.labelGraficos()[i])
                    ax.yaxis.grid(color='gray', linestyle='dashed')
                    ax.xaxis.grid(color='gray', linestyle='dashed')
                    ax.axhline(0, color='black', lw=2)
                    legend()
                    fig.savefig(base_path+base_dir+'residuos_fl'+str(self.__controleFluxo.FLUXO_ID)+'_versus_'+self.y.simbolos[i]+'_calculado.png')
                    close()

                    fig = figure()
                    ax = fig.add_subplot(1,1,1)
                    plot(self.y.validacao.matriz_estimativa[:,i],self.y.residuos.matriz_estimativa[:,i], 'o')
                    plot([min(self.y.validacao.matriz_estimativa[:,i]),max(self.y.validacao.matriz_estimativa[:,i])],[mean(self.y.residuos.matriz_estimativa[:,i])]*2, '-.r', label=u'Média resíduos '+self.y.simbolos[i])
                    ax.yaxis.grid(color='gray', linestyle='dashed')
                    ax.xaxis.grid(color='gray', linestyle='dashed')
                    ax.axhline(0, color='black', lw=2)
                    legend()
                    if self.__flag.info['dadosvalidacao']:
                        xlabel(u'Valores de validação '+self.y.labelGraficos()[i])
                        ylabel(u'Resíduos '+self.y.labelGraficos()[i])
                        fig.savefig(base_path+base_dir+'residuos_fl'+str(self.__controleFluxo.FLUXO_ID)+'_versus_'+self.y.simbolos[i]+'_validacao.png')
                    else:
                        xlabel(u'Valores de experimentais '+self.y.labelGraficos()[i])
                        ylabel(u'Resíduos '+self.y.labelGraficos()[i])
                        fig.savefig(base_path+base_dir+'residuos_fl'+str(self.__controleFluxo.FLUXO_ID)+'_versus_'+self.y.simbolos[i]+'_experimental.png')
                    close()

                    for j, simbol in enumerate(self.x.simbolos):
                        #X experimental vs. Resíduos
                        fig = figure()
                        ax = fig.add_subplot(1,1,1)
                        plot(self.x.experimental.matriz_estimativa[:,j],self.y.residuos.matriz_estimativa[:,i], 'o')
                        plot([min(self.x.experimental.matriz_estimativa[:,j]),max(self.x.experimental.matriz_estimativa[:,j])],[mean(self.y.residuos.matriz_estimativa[:,i])]*2, '-.r', label=u'Média resíduos '+self.y.simbolos[i])
                        xlabel(self.x.labelGraficos()[j] + ' experimental')
                        ylabel(u'Resíduos '+self.y.labelGraficos()[i])
                        ax.yaxis.grid(color='gray', linestyle='dashed')
                        ax.xaxis.grid(color='gray', linestyle='dashed')
                        ax.axhline(0, color='black', lw=2)
                        legend()
                        fig.savefig(base_path+base_dir+'residuos_fl'+str(self.__controleFluxo.FLUXO_ID)+'_versus_'+self.x.simbolos[j]+'_experimental.png')
                        close()

            else:
                warn('Os gráficos envolvendo a análise de resíduos não puderam ser criados, pois o método analiseResiduos não foi executado.',UserWarning)

    def relatorio(self,**kwargs):
        u"""
        Método para criação do(s) relatório(s) com os principais resultados.

        ========
        Keywords
        ========
        * Vide documentação de Relatorio.Predicao
        """
        # ---------------------------------------------------------------------
        # DEFINIÇÃO DA CLASSE
        # ---------------------------------------------------------------------
        saida = Relatorio(self.__base_path,sep +self._configFolder['relatorio']+ sep)

        # ---------------------------------------------------------------------
        # RELATÓRIO DOS PARÂMETROS
        # ---------------------------------------------------------------------
        # Caso a otimização ou SETParametros tenha sido executado, pode-se fazer um relatório sobre os parâmetros
        if self.__controleFluxo.otimizacao or self.__controleFluxo.SETparametro:
            saida.Parametros(self.parametros,self.FOotimo)
        else:
            warn('O relatório sobre os parâmetros não foi criado, pois o método otimizacao ou SETparametro não foi executado')
        # ---------------------------------------------------------------------
        # RELATÓRIO DA PREDIÇÃO E ANÁLISE DE RESÍDUOS
        # ---------------------------------------------------------------------
        # Caso a Predição tenha sido executada, pode-se fazer um relatório sobre a predição
        if self.__controleFluxo.predicao:
            # Caso a Análise de resíduos tenha sido executada, pode-se fazer um relatório completo
            if self.__controleFluxo.analiseResiduos:
                saida.Predicao(self.x,self.y,self.estatisticas,**kwargs)
            else:
                saida.Predicao(self.x,self.y,None,**kwargs)
                warn('O relatório sobre a análise de resíduos não foi criado, pois o método analiseResiduos não foi executado. Entretanto, ainda é possível exportar a predição')
        else:
            warn('O relatório sobre a predição e análise de resíduos não foi criado, pois o método predicao não foi executado')

        # ---------------------------------------------------------------------
        # RELATÓRIO DA PREDIÇÃO E ANÁLISE DE RESÍDUOS
        # ---------------------------------------------------------------------
        if self.__flag.info['relatoriootimizacao']:
            self.Otimizacao.Relatorios(base_path=self.__base_path + sep +self._configFolder['relatorio'] + sep,titulo_relatorio='relatorio-otimizacao.txt')