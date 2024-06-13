from flask import render_template, request, redirect, url_for, flash, abort,Blueprint,g
from flask_login import current_user, login_required
from datetime import datetime
from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SubmitField
from wtforms.validators import DataRequired

recipe_bp = Blueprint('recipe', __name__)

class RecipeForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired()])
    description = TextAreaField('Description')
    ingredients = TextAreaField('Ingredients', validators=[DataRequired()])
    instructions = TextAreaField('Instructions', validators=[DataRequired()])
    submit = SubmitField('Submit')

@recipe_bp.route('/recipes', methods=['GET'])
def list_recipes():
    cursor = g.db.cursor(dictionary=True)
    cursor.execute('''
        SELECT id, title, description
        FROM tbl_recipes
        WHERE user_id = %s
        ORDER BY created_at DESC
    ''', (current_user.id,))
    recipes = cursor.fetchall()
    cursor.close()
    return render_template('recipes/list.html', recipes=recipes)

@ recipe_bp.route('/recipes/<int:id>', methods=['GET'])
def view_recipe(id):
    cursor = g.db.cursor(dictionary=True)
    cursor.execute('SELECT * FROM tbl_recipes WHERE id = %s', (id,))
    recipe = cursor.fetchone()
    cursor.close()
    if recipe:
        return render_template('recipes/view.html', recipe=recipe)
    else:
        flash('Recipe not found.', 'danger')
        return redirect(url_for('list_recipes'))

@ recipe_bp.route('/recipes/create', methods=['GET', 'POST'])
@login_required
def create_recipe():
    form = RecipeForm()
    if form.validate_on_submit():
        title = form.title.data
        description = form.description.data
        ingredients = form.ingredients.data
        instructions = form.instructions.data

        cursor = g.db.cursor()
        cursor.execute('INSERT INTO tbl_recipes (user_id, title, description, ingredients, instructions) VALUES (%s, %s, %s, %s, %s)',
                       (current_user.id, title, description, ingredients, instructions))
        g.db.commit()
        cursor.close()

        flash('Recipe created successfully!', 'success')
        return redirect(url_for('recipe.list_recipes'))

    return render_template('recipes/form.html', form=form, action='Create')

@recipe_bp.route('/recipes/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit_recipe(id):
    cursor = g.db.cursor(dictionary=True)
    cursor.execute('SELECT * FROM tbl_recipes WHERE id = %s', (id,))
    recipe = cursor.fetchone()
    
    if not recipe:
        flash('Recipe not found.', 'danger')
        return redirect(url_for('recipe.list_recipes'))
    
    # Check if the current user is the owner of the recipe
    if recipe['user_id'] != current_user.id:
        abort(403)  # Forbidden
    
    form = RecipeForm(request.form)  # Create an empty form
    
    if request.method == 'POST' and form.validate():
        # Update the recipe dictionary with form data
        recipe.update({
            'title': request.form['title'],
            'description': request.form['description'],
            'ingredients': request.form['ingredients'],
            'instructions': request.form['instructions'],
            'updated_at': datetime.now()
        })
        
        # Perform the database update
        cursor.execute('UPDATE tbl_recipes SET title=%s, description=%s, ingredients=%s, instructions=%s, updated_at=%s WHERE id=%s',
                       (recipe['title'], recipe['description'], recipe['ingredients'], recipe['instructions'], recipe['updated_at'], id))
        g.db.commit()
        cursor.close()
        
        flash('Recipe updated successfully!', 'success')
        return redirect(url_for('recipe.list_recipes'))
    
    # Pre-populate the form with data from the recipe dictionary
    form.title.data = recipe['title']
    form.description.data = recipe['description']
    form.ingredients.data = recipe['ingredients']
    form.instructions.data = recipe['instructions']
    
    return render_template('recipes/form.html', form=form, action='Edit')

@ recipe_bp.route('/recipes/<int:id>/delete', methods=['POST'])
@login_required
def delete_recipe(id):
    cursor = g.db.cursor(dictionary=True)
    cursor.execute('SELECT * FROM tbl_recipes WHERE id = %s', (id,))
    recipe = cursor.fetchone()
    
    if not recipe:
        flash('Recipe not found.', 'danger')
        return redirect(url_for('list_recipes'))
    
    # Check if the current user is the owner of the recipe
    if recipe['user_id'] != current_user.id:
        abort(403)  # Forbidden
    
    cursor.execute('DELETE FROM tbl_recipes WHERE id = %s', (id,))
    g.db.commit()
    cursor.close()
    flash('Recipe deleted successfully!', 'success')
    return redirect(url_for('recipe.list_recipes'))
