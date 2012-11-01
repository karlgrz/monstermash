from flask.ext.assets import Bundle

js = Bundle('vendor/jquery/jquery-1.8.2.min.js', 'vendor/bootstrap/bootstrap.min.js', output='gen/packed.js')
css = Bundle('vendor/bootstrap/bootstrap.min.css', 'css/monstermash.css', output='gen/packed.css')
