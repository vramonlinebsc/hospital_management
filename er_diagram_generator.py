"""
Generate ER Diagram for Hospital Management System
"""
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
import matplotlib.lines as mlines

# Create figure
fig, ax = plt.subplots(1, 1, figsize=(16, 12))
ax.set_xlim(0, 16)
ax.set_ylim(0, 12)
ax.axis('off')

# Define colors
entity_color = '#4A90E2'
attribute_color = '#F5F5F5'
relationship_color = '#E8B44E'
text_color = '#2C3E50'

def create_entity(ax, x, y, width, height, name, attributes, primary_key):
    """Create an entity rectangle with attributes"""
    # Main entity box
    entity_box = FancyBboxPatch((x, y), width, height,
                                boxstyle="round,pad=0.05", 
                                edgecolor=entity_color, 
                                facecolor=entity_color,
                                linewidth=2.5)
    ax.add_patch(entity_box)
    
    # Entity name
    ax.text(x + width/2, y + height - 0.25, name,
            ha='center', va='center', fontsize=13, fontweight='bold',
            color='white')
    
    # Attributes box
    attr_height = len(attributes) * 0.22 + 0.2
    attr_box = FancyBboxPatch((x, y - attr_height), width, attr_height,
                             boxstyle="round,pad=0.02",
                             edgecolor=entity_color,
                             facecolor=attribute_color,
                             linewidth=1.5)
    ax.add_patch(attr_box)
    
    # Draw attributes
    y_offset = y - 0.25
    for attr in attributes:
        if attr == primary_key:
            text = f"🔑 {attr}"
            weight = 'bold'
        elif 'FK' in attr or 'UNIQUE' in attr or 'INDEXED' in attr:
            text = attr
            weight = 'bold'
        else:
            text = attr
            weight = 'normal'
        
        ax.text(x + 0.15, y_offset, text,
                ha='left', va='center', fontsize=8, fontweight=weight,
                color=text_color)
        y_offset -= 0.22

def create_relationship(ax, x1, y1, x2, y2, label, cardinality1, cardinality2):
    """Create a relationship line between entities"""
    # Draw line
    arrow = FancyArrowPatch((x1, y1), (x2, y2),
                           arrowstyle='-',
                           linewidth=2.5,
                           color=relationship_color)
    ax.add_patch(arrow)
    
    # Relationship label
    mid_x, mid_y = (x1 + x2) / 2, (y1 + y2) / 2
    ax.text(mid_x, mid_y + 0.2, label,
            ha='center', va='bottom', fontsize=9, fontweight='bold',
            bbox=dict(boxstyle='round,pad=0.3', facecolor='white', 
                     edgecolor=relationship_color, linewidth=1.5),
            color=text_color)
    
    # Cardinality labels
    ax.text(x1 + (x2-x1)*0.15, y1 + (y2-y1)*0.15, cardinality1,
            ha='center', va='center', fontsize=10, fontweight='bold',
            color=relationship_color)
    ax.text(x2 - (x2-x1)*0.15, y2 - (y2-y1)*0.15, cardinality2,
            ha='center', va='center', fontsize=10, fontweight='bold',
            color=relationship_color)

# Create entities with their attributes

# USER entity (center top)
user_attrs = [
    'id (PK)',
    'username (UNIQUE, INDEXED)',
    'email (UNIQUE, INDEXED)',
    'password_hash',
    'role',
    'is_active',
    'created_at',
    'updated_at'
]
create_entity(ax, 6.5, 9.5, 3, 0.7, 'USER', user_attrs, 'id')

# DOCTOR entity (left middle)
doctor_attrs = [
    'id (PK)',
    'user_id (FK, UNIQUE)',
    'full_name',
    'specialization (INDEXED)',
    'qualification',
    'experience_years',
    'contact_number',
    'license_number (UNIQUE)',
    'consultation_fee',
    'bio',
    'is_active',
    'is_deleted',
    'created_at',
    'updated_at'
]
create_entity(ax, 0.5, 5.5, 3.2, 0.7, 'DOCTOR', doctor_attrs, 'id')

# PATIENT entity (right middle)
patient_attrs = [
    'id (PK)',
    'user_id (FK, UNIQUE)',
    'full_name',
    'date_of_birth',
    'gender',
    'blood_group',
    'contact_number',
    'address',
    'emergency_contact_name',
    'emergency_contact_number',
    'medical_history',
    'allergies',
    'is_active',
    'is_deleted',
    'created_at',
    'updated_at'
]
create_entity(ax, 12.3, 5.5, 3.2, 0.7, 'PATIENT', patient_attrs, 'id')

# APPOINTMENT entity (center middle)
appointment_attrs = [
    'id (PK)',
    'patient_id (FK)',
    'doctor_id (FK)',
    'appointment_date (INDEXED)',
    'appointment_time',
    'status',
    'reason',
    'notes',
    'is_deleted',
    'created_at',
    'updated_at'
]
create_entity(ax, 6.3, 3.5, 3.4, 0.7, 'APPOINTMENT', appointment_attrs, 'id')

# TREATMENT entity (center bottom)
treatment_attrs = [
    'id (PK)',
    'appointment_id (FK, UNIQUE)',
    'diagnosis',
    'prescription',
    'test_recommended',
    'notes',
    'follow_up_required',
    'follow_up_date',
    'created_at',
    'updated_at'
]
create_entity(ax, 6.5, 0.3, 3, 0.7, 'TREATMENT', treatment_attrs, 'id')

# DOCTOR_AVAILABILITY entity (left bottom)
availability_attrs = [
    'id (PK)',
    'doctor_id (FK)',
    'available_date (INDEXED)',
    'start_time',
    'end_time',
    'is_available',
    'created_at'
]
create_entity(ax, 0.3, 1.5, 3.5, 0.7, 'DOCTOR_AVAILABILITY', availability_attrs, 'id')

# Create relationships
# USER to DOCTOR (1:1)
create_relationship(ax, 7.2, 9.5, 2.8, 6.2, 'has', '1', '0..1')

# USER to PATIENT (1:1)
create_relationship(ax, 8.8, 9.5, 13.2, 6.2, 'has', '1', '0..1')

# PATIENT to APPOINTMENT (1:N)
create_relationship(ax, 13, 5.5, 8.5, 4.2, 'books', '1', 'N')

# DOCTOR to APPOINTMENT (1:N)
create_relationship(ax, 3, 5.5, 7, 4.2, 'attends', '1', 'N')

# APPOINTMENT to TREATMENT (1:1)
create_relationship(ax, 8, 3.5, 8, 1.0, 'generates', '1', '1')

# DOCTOR to DOCTOR_AVAILABILITY (1:N)
create_relationship(ax, 2.1, 5.5, 2.1, 2.2, 'provides', '1', 'N')

# Add title
ax.text(8, 11.5, 'Hospital Management System - Entity Relationship Diagram',
        ha='center', va='center', fontsize=18, fontweight='bold',
        color=text_color)

# Add legend
legend_elements = [
    mpatches.Rectangle((0, 0), 1, 1, fc=entity_color, label='Entity'),
    mpatches.Rectangle((0, 0), 1, 1, fc=attribute_color, edgecolor=entity_color, label='Attributes'),
    mlines.Line2D([], [], color=relationship_color, linewidth=2.5, label='Relationship')
]
ax.legend(handles=legend_elements, loc='lower right', fontsize=10)

# Add notes
notes_text = (
    "Notes:\n"
    "• PK = Primary Key, FK = Foreign Key\n"
    "• UNIQUE = Unique constraint\n"
    "• INDEXED = Database index for performance\n"
    "• Cardinality: 1 = one, N = many, 0..1 = optional one"
)
ax.text(0.5, 11.3, notes_text, ha='left', va='top', fontsize=8,
        bbox=dict(boxstyle='round,pad=0.5', facecolor='#FFFACD', alpha=0.8),
        color=text_color)

plt.tight_layout()
plt.savefig('/home/ubuntu/hospital_management_system/er_diagram.png', 
            dpi=300, bbox_inches='tight', facecolor='white')
print("ER Diagram generated successfully!")
