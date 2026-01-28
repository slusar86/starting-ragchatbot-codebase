/**
 * Claude AI Integration for RAG Chatbot Frontend
 * Provides additional Claude capabilities for the chat interface
 */

class ClaudeRAGIntegration {
    constructor(apiKey) {
        this.apiKey = apiKey;
        this.apiUrl = 'https://api.anthropic.com/v1/messages';
        this.model = 'claude-3-5-sonnet-20241022';
        this.enableAllFeatures = true;
        this.conversationHistory = [];
    }

    /**
     * Send a message and get Claude's response
     * @param {string} message - User message
     * @param {string} context - Optional context from RAG system
     * @returns {Promise<string>} - Claude's response
     */
    async sendMessage(message, context = '') {
        try {
            // Add user message to history
            this.conversationHistory.push({
                role: 'user',
                content: this.formatUserMessage(message, context)
            });

            const response = await fetch(this.apiUrl, {
                method: 'POST',
                headers: {
                    'x-api-key': this.apiKey,
                    'anthropic-version': '2023-06-01',
                    'content-type': 'application/json',
                },
                body: JSON.stringify({
                    model: this.model,
                    max_tokens: 2000,
                    system: this.getSystemPrompt(),
                    messages: this.conversationHistory
                })
            });

            if (!response.ok) {
                const error = await response.json();
                console.error('Claude API error:', error);
                throw new Error(`API error: ${response.status}`);
            }

            const data = await response.json();
            const assistantMessage = data.content[0].text;

            // Add assistant response to history
            this.conversationHistory.push({
                role: 'assistant',
                content: assistantMessage
            });

            // Keep conversation history manageable (last 10 exchanges)
            if (this.conversationHistory.length > 20) {
                this.conversationHistory = this.conversationHistory.slice(-20);
            }

            return assistantMessage;
        } catch (error) {
            console.error('Error communicating with Claude:', error);
            throw error;
        }
    }

    /**
     * Format user message with RAG context
     */
    formatUserMessage(message, context) {
        if (context) {
            return `Context from course materials:\n${context}\n\nUser question: ${message}`;
        }
        return message;
    }

    /**
     * Get system prompt for course assistant
     */
    getSystemPrompt() {
        return `You are a helpful Course Materials Assistant powered by Claude AI. Your role is to:
1. Answer questions about courses, lessons, instructors, and course content
2. Provide clear, concise explanations
3. Organize information in an easy-to-understand format
4. Reference specific courses and lessons when relevant
5. Suggest related topics the user might find interesting

Guidelines:
- Be friendly and professional
- If you're unsure about something, say so
- Encourage learning and curiosity
- Keep responses focused and relevant to the course materials
- Use formatting (bullet points, numbering) to make responses clear`;
    }

    /**
     * Clear conversation history
     */
    clearHistory() {
        this.conversationHistory = [];
    }

    /**
     * Get a summary of the current conversation
     */
    async getSummary() {
        if (this.conversationHistory.length === 0) {
            return 'No conversation yet.';
        }

        try {
            const response = await fetch(this.apiUrl, {
                method: 'POST',
                headers: {
                    'x-api-key': this.apiKey,
                    'anthropic-version': '2023-06-01',
                    'content-type': 'application/json',
                },
                body: JSON.stringify({
                    model: this.model,
                    max_tokens: 300,
                    messages: [
                        {
                            role: 'user',
                            content: `Summarize this conversation in 2-3 sentences:\n\n${this.formatConversationForSummary()}`
                        }
                    ]
                })
            });

            if (!response.ok) throw new Error('Summary failed');
            const data = await response.json();
            return data.content[0].text;
        } catch (error) {
            console.error('Error getting summary:', error);
            return 'Could not generate summary.';
        }
    }

    /**
     * Format conversation for summary
     */
    formatConversationForSummary() {
        return this.conversationHistory
            .map(msg => `${msg.role}: ${msg.content}`)
            .join('\n');
    }

    /**
     * Get suggested follow-up questions based on conversation
     */
    async getSuggestedQuestions() {
        if (this.conversationHistory.length === 0) {
            return [];
        }

        try {
            const response = await fetch(this.apiUrl, {
                method: 'POST',
                headers: {
                    'x-api-key': this.apiKey,
                    'anthropic-version': '2023-06-01',
                    'content-type': 'application/json',
                },
                body: JSON.stringify({
                    model: this.model,
                    max_tokens: 200,
                    messages: [
                        {
                            role: 'user',
                            content: `Based on this conversation, suggest 3 follow-up questions (one per line, no numbering):\n\n${this.formatConversationForSummary()}`
                        }
                    ]
                })
            });

            if (!response.ok) throw new Error('Suggestions failed');
            const data = await response.json();
            return data.content[0].text.split('\n').filter(q => q.trim());
        } catch (error) {
            console.error('Error getting suggestions:', error);
            return [];
        }
    }
}
