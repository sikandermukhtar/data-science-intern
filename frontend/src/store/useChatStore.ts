import { create } from 'zustand';
import type { Message, ChatSession, FileAttachment } from '@/types/chat';

interface ChatState {
    sessions: ChatSession[];
    activeSessionId: string | null;
    messages: Record<string, Message[]>;
    isLoading: boolean;
    setCurrentSession: (sessionId: string) => void;
    createNewSession: () => void;
    sendMessage: (content: string, files?: File[]) => void;
}

export const useChatStore = create<ChatState>((set, get) => {
    
    const dummySessionId = 'dummy-session-1';
    const dummyMessages: Message[] = [
        {
            id: 'm1',
            role: 'user',
            content: 'Hey, I uploaded `diabetes.csv`. Can you run a correlation analysis on the features and show me the distribution of the outcome variable?',
            files: [
                { name: 'diabetes.csv', size: 23840, type: 'text/csv' }
            ],
            timestamp: Date.now() - 3600000 * 2,
        },
        {
            id: 'm2',
            role: 'assistant',
            content: `I have loaded the \`diabetes.csv\` dataset. Let's perform a correlation analysis of the feature columns and plot the heatmap, along with the distribution of the target \`Outcome\` column.

### Dataset Overview
Here is a summary of the first few rows and types:

| Column | Non-Null Count | Dtype | Description |
| :--- | :--- | :--- | :--- |
| **Pregnancies** | 768 non-null | int64 | Number of times pregnant |
| **Glucose** | 768 non-null | int64 | Plasma glucose concentration |
| **BloodPressure** | 768 non-null | int64 | Diastolic blood pressure (mm Hg) |
| **BMI** | 768 non-null | float64 | Body mass index (weight in kg/(height in m)^2) |
| **Age** | 768 non-null | int64 | Age (years) |
| **Outcome** | 768 non-null | int64 | Class variable (0 or 1) |

Below is the Python script used to compute the correlations and plot the charts:`,
            timestamp: Date.now() - 3600000 * 2 + 5000,
        },
        {
            id: 'm3',
            role: 'assistant',
            content: `\`\`\`python
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt

# Load dataset
df = pd.read_csv('diabetes.csv')

# Compute correlation matrix
corr = df.corr()

# Plot heatmap
plt.figure(figsize=(10, 8))
sns.heatmap(corr, annot=True, cmap='coolwarm', fmt='.2f')
plt.title('Correlation Matrix of Diabetes Features')
plt.savefig('correlation_heatmap.png')
plt.close()

# Plot outcome distribution
plt.figure(figsize=(6, 4))
sns.countplot(x='Outcome', data=df, palette='Set2')
plt.title('Distribution of Diabetic Outcome')
plt.savefig('outcome_distribution.png')
plt.close()
\`\`\`

Here are the generated visualizations:`,
            timestamp: Date.now() - 3600000 * 2 + 10000,
        },
        {
            id: 'm4',
            role: 'assistant',
            content: '---charts---', 
            files: [
                {
                    name: 'correlation_heatmap.png',
                    size: 45210,
                    type: 'image/png',
                    url: '/correlation_heatmap.png'
                },
                {
                    name: 'feature_importance.png',
                    size: 32410,
                    type: 'image/png',
                    url: '/outcome_distribution.png'
                }
            ],
            timestamp: Date.now() - 3600000 * 2 + 12000,
        }
    ];

    return {
        sessions: [
            { id: dummySessionId, title: 'Analyze diabetes.csv', updatedAt: Date.now() }
        ],
        activeSessionId: dummySessionId,
        messages: {
            [dummySessionId]: dummyMessages
        },
        isLoading: false,

        setCurrentSession: (sessionId) => set({ activeSessionId: sessionId }),

        createNewSession: () => {
            const newSessionId = `session-${Date.now()}`;
            const newSession: ChatSession = {
                id: newSessionId,
                title: 'New Session',
                updatedAt: Date.now(),
            };
            set((state) => ({
                sessions: [newSession, ...state.sessions],
                activeSessionId: newSessionId,
                messages: {
                    ...state.messages,
                    [newSessionId]: []
                }
            }));
        },

        sendMessage: (content, files) => {
            const { activeSessionId, messages } = get();
            if (!activeSessionId) return;

            const sessionMessages = messages[activeSessionId] || [];

            
            const userFiles: FileAttachment[] = files ? files.map(f => ({
                name: f.name,
                size: f.size,
                type: f.type,
                url: URL.createObjectURL(f)
            })) : [];

            const userMsg: Message = {
                id: `u-${Date.now()}`,
                role: 'user',
                content,
                files: userFiles.length > 0 ? userFiles : undefined,
                timestamp: Date.now(),
            };

            set((state) => ({
                messages: {
                    ...state.messages,
                    [activeSessionId]: [...sessionMessages, userMsg]
                },
                isLoading: true,
            }));

            
            setTimeout(() => {
                const updatedMessages = get().messages[activeSessionId] || [];
                const responseMsg: Message = {
                    id: `a-${Date.now()}`,
                    role: 'assistant',
                    content: `Here is the evaluation response to your query: **"${content}"**.

As your Data Science Intern, I have simulated a backend run on your data. Here is a sample metric distribution:

| Metric | Score | Status |
| :--- | :--- | :--- |
| **Accuracy** | 0.89 | Optimal |
| **Precision** | 0.86 | Stable |
| **Recall** | 0.91 | Excellent |

Here is the classification evaluation script:
\`\`\`python
# Evaluated model performance
from sklearn.metrics import classification_report

print(classification_report(y_true, y_pred))
\`\`\`

Here is the confusion matrix chart generated from the evaluation:`,
                    timestamp: Date.now(),
                };

                const chartMsg: Message = {
                    id: `a-chart-${Date.now()}`,
                    role: 'assistant',
                    content: '---charts---',
                    files: [
                        {
                            name: 'confusion_matrix.png',
                            size: 29810,
                            type: 'image/png',
                            url: '/confusion_matrix.png'
                        }
                    ],
                    timestamp: Date.now() + 500
                };

                set((state) => ({
                    messages: {
                        ...state.messages,
                        [activeSessionId]: [...updatedMessages, responseMsg, chartMsg]
                    },
                    isLoading: false,
                }));
            }, 1500);
        }
    };
});