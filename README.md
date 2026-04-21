# 🚀 LangGraph: Agente Matemático com Gemini 1.5

<p align="center">
  <video src="default.mp4" width="100%" style="max-width:800px;" controls autoplay muted loop>
    Seu navegador não suporta o elemento de vídeo.
  </video>
</p>

Este repositório contém um exemplo prático de como construir um **Agente Inteligente** utilizando **LangGraph** e **LangChain**, integrados ao modelo **Gemini 1.5 Flash**. O agente é capaz de raciocinar sobre uma pergunta matemática, decidir quais ferramentas usar, executar códigos Python e retornar uma resposta final precisa.

---

## 🧠 O que é este projeto?

Diferente de um Chatbot comum que apenas "conversa", este projeto implementa um **Agente Reativo (ReAct)**. Ele não tenta calcular equações complexas "de cabeça" (onde os LLMs podem cometer erros de cálculo); em vez disso, ele utiliza **ferramentas (tools)** de Python para garantir precisão matemática absoluta.

---

## 🛠️ Arquitetura do Grafo

O fluxo de trabalho é definido por um **Grafo de Estados** (`StateGraph`). Cada nó representa uma etapa da inteligência ou da ação:



1.  **START**: O ponto de entrada onde a pergunta do utilizador é recebida.
2.  **llm_call (O Cérebro)**: O Gemini analisa o histórico e decide: "Preciso de uma calculadora ou posso responder agora?".
3.  **should_continue (O Decisor)**: Uma aresta condicional que verifica se o modelo gerou pedidos de ferramentas (`tool_calls`).
4.  **tool_node (As Mãos)**: O Python executa a função real (soma, multiplicação ou divisão).
5.  **Ciclo de Retroalimentação**: O resultado da ferramenta é anexado ao estado e o fluxo volta para o LLM, que reavalia se precisa de mais alguma conta até chegar à resposta final (**END**).

---

## 📖 Detalhamento Técnico

### 1. O Sistema de Memória: `MessagesState`
O estado é o "quadro branco" onde o agente anota tudo o que aconteceu.
```python
class MessagesState(TypedDict):
    messages: Annotated[list[AnyMessage], operator.add]
    llm_calls: int
```

```operator.add:``` Este é o segredo do LangGraph. Ele garante que as novas mensagens (respostas do AI ou resultados de ferramentas) sejam acumuladas na lista, permitindo que o agente tenha memória de curto prazo.

### 2. O Nó do Modelo (llm_call)
Este nó é onde a lógica de IA reside.

```bind_tools```: Nós "emprestamos" as nossas funções Python ao Gemini. Através das definições das funções, o Gemini entende quando e como chamar cada uma.

**Prompt de Sistema:** Definimos que o modelo é um assistente especializado em aritmética para manter o foco na tarefa.

### 3. O Nó de Ferramentas (tool_node)
Este nó é puramente funcional. Ele lê o pedido da IA (ex: multiply(```a=10```, ```b=200```)), executa a função correspondente e cria uma ```ToolMessage```. Esta mensagem serve para dizer ao modelo: _"Aqui está o resultado que me pediste"_.

### 📊 Análise do Resultado no Terminal

_Console do terminal CMD:_
```cmd
================================ Human Message =================================

10 vezes 200, dividido por 4, quanto é?
================================== Ai Message ==================================
Tool Calls:
  multiply (f8c5efac-ecd9-4715-b62e-a4ae233c7d8a)
 Call ID: f8c5efac-ecd9-4715-b62e-a4ae233c7d8a
  Args:
    a: 10
    b: 200
================================= Tool Message =================================

2000
================================== Ai Message ==================================
Tool Calls:
  divide (1d35888e-155c-4a70-96ef-c7b6d5c8dae3)
 Call ID: 1d35888e-155c-4a70-96ef-c7b6d5c8dae3
  Args:
    a: 2000
    b: 4
================================= Tool Message =================================
```
Ao enviar a pergunta: "10 vezes 200, dividido por 4, quanto é?", o agente seguiu estes passos invisíveis:

| Passo | Agente | Estado (Memória) | Ação |
| :--- | :--- | :--- | :--- |
| **1** | **Humano** | Pergunta original | Inicia o Grafo. |
| **2** | **Gemini** | Pergunta + Pedido de Ferramenta | Identifica que deve multiplicar 10 por 200. |
| **3** | **Python** | Resultado: 2000 | Executa `multiply` e devolve o valor. |
| **4** | **Gemini** | Histórico + 2000 + Pedido de Ferramenta | Vê o 2000 e pede para dividir por 4. |
| **5** | **Python** | Resultado: 500 | Executa `divide` e devolve o valor. |
| **6** | **Gemini** | Resposta Final | Vê que não há mais contas e responde ao utilizador. |