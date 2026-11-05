# D:\project\new\crimenet\quick_fix.py
import os
import glob

def fix_templates():
    print("Starting template fix...")
    
    # Find all HTML templates in the crimes app
    template_patterns = [
        "crimes/templates/crimes/*.html",
        "crimes/templates/crimes/**/*.html",  # For subdirectories
    ]
    
    for pattern in template_patterns:
        templates = glob.glob(pattern, recursive=True)
        
        for template in templates:
            print(f"Processing: {template}")
            
            try:
                with open(template, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                changes_made = False
                
                # 1. Remove crispy forms load tag
                if "{% load crispy_forms_tags %}" in content:
                    content = content.replace("{% load crispy_forms_tags %}", "")
                    changes_made = True
                    print(f"  - Removed crispy_forms_tags")
                
                # 2. Replace form|crispy with simple form rendering
                if "{{ form|crispy }}" in content:
                    content = content.replace("{{ form|crispy }}", """
                    <div class="form-container">
                    {% for field in form %}
                        <div class="mb-3">
                            <label class="form-label">{{ field.label }}</label>
                            {{ field }}
                            {% if field.help_text %}
                            <div class="form-text text-muted">{{ field.help_text }}</div>
                            {% endif %}
                            {% if field.errors %}
                            <div class="text-danger small">
                                {% for error in field.errors %}
                                <div>{{ error }}</div>
                                {% endfor %}
                            </div>
                            {% endif %}
                        </div>
                    {% endfor %}
                    </div>
                    """)
                    changes_made = True
                    print(f"  - Replaced form|crispy")
                
                # 3. Also check for other crispy forms syntax
                if "{% crispy" in content:
                    # This handles {% crispy form %} syntax
                    import re
                    content = re.sub(r'\{%\s*crispy.*?%\}', """
                    <div class="form-container">
                    {% for field in form %}
                        <div class="mb-3">
                            <label class="form-label">{{ field.label }}</label>
                            {{ field }}
                            {% if field.help_text %}
                            <div class="form-text">{{ field.help_text }}</div>
                            {% endif %}
                        </div>
                    {% endfor %}
                    </div>
                    """, content)
                    changes_made = True
                    print(f"  - Replaced crispy tag")
                
                if changes_made:
                    with open(template, 'w', encoding='utf-8') as f:
                        f.write(content)
                    print(f"  ✓ Updated: {template}")
                else:
                    print(f"  - No changes needed")
                    
            except Exception as e:
                print(f"  ✗ Error processing {template}: {e}")
    
    print("\n" + "="*50)
    print("✅ Template fixing complete!")
    print("="*50)
    print("\nNext steps:")
    print("1. Restart your Django server")
    print("2. Refresh your browser")
    print("3. If errors persist, check if templates still reference crispy forms")

if __name__ == "__main__":
    fix_templates()