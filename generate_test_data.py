import pandas as pd
import random
from datetime import datetime

# Define categories and their subcategories
categories = {
    'الخدمات': [
        'خدمات رقمية', 'البنية التقنية', 'السكن', 'الطعام', 'النقل'
    ],
    'الدعم الطلابي': [
        'الإرشاد الأكاديمي', 'الخدمات الصحية', 'الأنشطة', 
        'الخدمات الإدارية', 'دعم الطلاب الدوليين'
    ],
    'المرافق': [
        'المكتبة', 'المختبرات', 'المرافق الرياضية', 'أماكن الدراسة'
    ],
    'المناهج': [
        'مقررات', 'برنامج', 'عضو هيئة تدريس'
    ]
}

# Sample responses for each category
sample_responses = {
    'الخدمات': {
        'خدمات رقمية': [
            "البوابة الإلكترونية سهلة الاستخدام وتوفر جميع الخدمات التي أحتاجها",
            "التطبيق الجامعي بطيء جداً ويحتاج إلى تحديث",
            "خدمة الإنترنت في الحرم الجامعي ممتازة وسريعة"
        ],
        'البنية التقنية': [
            "شبكة الواي فاي تغطي جميع مناطق الجامعة",
            "أجهزة الحاسب في المعامل قديمة وبطيئة",
            "نظام التعليم عن بعد يعمل بشكل جيد"
        ],
        'السكن': [
            "السكن الجامعي نظيف ومريح",
            "الغرف صغيرة جداً ولا تكفي للدراسة",
            "خدمات الصيانة في السكن سريعة وفعالة"
        ],
        'الطعام': [
            "الكافتيريا توفر وجبات صحية ومتنوعة",
            "أسعار الطعام مرتفعة جداً",
            "جودة الطعام في المطعم الجامعي سيئة"
        ],
        'النقل': [
            "حافلات الجامعة منتظمة ومريحة",
            "مواقف السيارات بعيدة عن المباني",
            "خدمة النقل الجامعي غير كافية"
        ]
    },
    'الدعم الطلابي': {
        'الإرشاد الأكاديمي': [
            "المرشد الأكاديمي متعاون ويساعدني في اختيار المواد",
            "صعب الوصول للمرشد الأكاديمي",
            "نظام الإرشاد الأكاديمي غير فعال"
        ],
        'الخدمات الصحية': [
            "العيادة الطبية مجهزة بشكل جيد",
            "فترة الانتظار في العيادة طويلة جداً",
            "الطاقم الطبي متعاون ومحترف"
        ],
        'الأنشطة': [
            "الأنشطة الطلابية متنوعة وممتعة",
            "قلة الفعاليات الثقافية في الجامعة",
            "النوادي الطلابية نشيطة ومفيدة"
        ]
    },
    'المرافق': {
        'المكتبة': [
            "المكتبة غنية بالمراجع وهادئة",
            "ساعات عمل المكتبة غير كافية",
            "نظام البحث في المكتبة معقد"
        ],
        'المختبرات': [
            "المختبرات مجهزة بأحدث المعدات",
            "المعامل تحتاج إلى صيانة",
            "عدد المختبرات غير كافٍ"
        ]
    },
    'المناهج': {
        'مقررات': [
            "المقررات تواكب سوق العمل",
            "بعض المواد صعبة جداً",
            "المحتوى التعليمي ممتاز"
        ],
        'برنامج': [
            "البرنامج منظم بشكل جيد",
            "الخطة الدراسية تحتاج إلى تحديث",
            "متطلبات التخرج واضحة"
        ]
    }
}

# Non-related examples
non_related_examples = [
    "I love playing video games after school",
    "The weather is beautiful today",
    "My favorite color is blue",
    "Yesterday I went to the cinema",
    "Je vais à la plage ce weekend",
    "Ich liebe Musik",
    "私は日本語を勉強しています",
    "안녕하세요",
    "123456789",
    "!@#$%^&*()",
    "",  # Empty string
    " ",  # Just space
    "N/A",
    "null",
    "undefined"
]

# Edge cases
edge_cases = [
    "ا" * 1000,  # Very long text
    "تجربة" * 100,
    "\n\n\n\n",  # Multiple newlines
    "تجربة\nسطر\nجديد",  # Text with newlines
    "<script>alert('XSS')</script>",  # Potential XSS
    "DROP TABLE students;",  # SQL injection attempt
    "١٢٣٤٥٦٧٨٩٠",  # Arabic numerals
    "مرحباً 👋 بكم 🎓 في 🏫 الجامعة",  # Text with emojis
    "تجربة; تجربة, تجربة",  # Text with special characters
    "    تجربة    ",  # Text with extra spaces
]

def generate_response():
    """Generate a random response with various possibilities."""
    choice = random.random()
    
    if choice < 0.7:  # 70% related responses
        category = random.choice(list(categories.keys()))
        subcategory = random.choice(categories[category])
        if category in sample_responses and subcategory in sample_responses[category]:
            return random.choice(sample_responses[category][subcategory])
        return f"تجربة متعلقة بـ {subcategory} في {category}"
    elif choice < 0.85:  # 15% non-related
        return random.choice(non_related_examples)
    else:  # 15% edge cases
        return random.choice(edge_cases)

# Generate 100 responses
responses = [generate_response() for _ in range(100)]

# Save as TXT
with open('test_data.txt', 'w', encoding='utf-8') as f:
    for response in responses:
        f.write(response + '\n')

# Save as CSV
df = pd.DataFrame({
    'Response': responses,
    'Timestamp': [datetime.now().strftime("%Y-%m-%d %H:%M:%S")] * len(responses)
})
df.to_csv('test_data.csv', index=False, encoding='utf-8-sig')

# Save as Excel
df.to_excel('test_data.xlsx', index=False, engine='openpyxl')

print("Test data generated successfully in three formats:"
      "\n1. test_data.txt"
      "\n2. test_data.csv"
      "\n3. test_data.xlsx") 