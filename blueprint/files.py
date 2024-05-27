from flask import Blueprint, render_template, redirect, url_for, request, session, Response, send_file
# from src.User import User
from src.Database import Database
from gridfs import GridFS, GridFSBucket
import mimetypes
from blueprint import user
import uuid
from werkzeug.utils import secure_filename

bp = Blueprint("files", __name__, url_prefix="/v1/api/files")
db = Database.get_connection()
collection = db.employees

@bp.route('/upload', methods=['POST'])
def upload_bucket():
    if 'file' in request.files and 'ticket_id' in request.form:
        file = request.files['file']
        ticket_id = request.form['ticket_id']
        fs = GridFSBucket(Database.get_connection())
        
        metadata = {
            'original_filename': file.filename,
            'content_type': mimetypes.guess_type(file.filename)[0],
            'ticket_id': ticket_id
        }
        
        filename = str(uuid.uuid4())
        username=session.get('name')
        
        file_id = fs.upload_from_stream(filename, file, metadata=metadata)
        return {
            'message': "Upload Success",
            'file_id': str(file_id),
            'filename': filename,
            'ticket_id': ticket_id,
            'download_url': '/v1/api/files/download/'+filename,
            'stream_url': '/v1/api/files/stream/'+filename,
            'get_url': '/v1/api/files/get/'+filename,
            'type': 'success'
        }, 200
    else:
        return {
            'message': 'Bad Request',
            'type': 'error'
        }, 400

@bp.route('/avatar', methods=['POST'])
def uploadket():
    if 'file' in request.files :
        file = request.files['file']
        fs = GridFSBucket(Database.get_connection())
        username=session.get('name')
        metadata = {
            'original_filename': file.filename,
            'content_type': mimetypes.guess_type(file.filename)[0],
            'uploaded_by': username
        }
        
        filename = str(uuid.uuid4())
        
        file_id = fs.upload_from_stream(filename, file, metadata=metadata)

        query = {"name": username}
        new_values = {"$set": {"avatar": filename}}
    
        collection.update_one(query, new_values)
  
        return redirect(url_for('user.profiles'))
    else:
        return {
            'message': 'Bad Request',
            'type': 'error'
        }, 400
        
@bp.route('/get/<filename>', methods=['GET'])
def get_bucket(filename):
    if session.get('authenticated'):
        try:
            fs = GridFSBucket(Database.get_connection())
            file = fs.open_download_stream_by_name(filename)
            response = Response(file.read(), status=200, mimetype=file.metadata['content_type'])
            return response
        except: 
            return {
                'message': 'File not found',
                'type': 'error'
            }, 404
    else:
        return {
            'message': 'Bad Request',
            'type': 'error'
        }, 400
        
@bp.route('/download/<filename>', methods=['GET'])
def get_fs(filename):
    if session.get('authenticated'):
        fs = GridFS(Database.get_connection())
        file = fs.find_one({
            'filename': secure_filename(filename)
        })
        if file is None:
            return {
                'message': 'File not found',
                'type': 'error'
            }, 404

        return send_file(file, mimetype=file.metadata['content_type'], as_attachment=True, download_name=file.metadata['original_filename'])
    else:
        return {
            'message': 'Bad Request',
            'type': 'error'
        }, 400

@bp.route('/put', methods=['POST'])
def put_fs():
    if 'file' in request.files and session.get('authenticated'):
        fs = GridFS(Database.get_connection())
        file = request.files['file']
        filename = str(uuid.uuid4())
        metadata = {
            'original_filename': file.filename,
            'content_type': mimetypes.guess_type(file.filename)[0],
            'owner': session.get('username')
        }
        file_id = fs.put(file, filename=filename, metadata=metadata)
        return {
            'message': "Upload Success",
            'file_id': str(file_id),
            'filename': filename,
            'download_url': '/files/download/'+filename,
            'stream_url': '/files/stream/'+filename,
            'get_url': '/files/get/'+filename,
            'type': 'success'
        }, 200
    else:
        return {
            'message': 'Bad Request',
            'type': 'error'
        }, 400
        
@bp.route('/stream/<filename>', methods=['GET'])
def stream_fs(filename):
    db = Database.get_connection()
    file_doc = db.fs.files.find_one({
        'filename': filename
    })
    
    if file_doc is None:
         return {
                'message': 'File not found',
                'type': 'error'
            }, 404
    
    total_size = file_doc['length']
    chunk_size = file_doc['chunkSize']
    mime_type = file_doc['metadata']['content_type']
    
    range_header = request.headers.get('Range', None)
    if not range_header:
        start = 0
        end = chunk_size - 1
    else:
        range_bytes = range_header.split("=")[1]
        range_split = range_bytes.split("-")
        start = int(range_split[0])
        end = int(range_split[1])
        
    start_chunk = start // chunk_size
    end_chunk = end // chunk_size
    
    def stream():
        for chunk_number in range(start_chunk, end_chunk + 1): # +1 because range is exclusive
            chunk = db.fs.chunks.find_one({
                'files_id': file_doc['_id'],
                'n': chunk_number
            })
            start_index = max(0, start - (chunk_number * chunk_size))
            end_index = min(chunk_size, end - (chunk_number * chunk_size) + 1)
            yield chunk['data'][start_index:end_index]
            
    response = Response(stream(), status=206, mimetype=mime_type, direct_passthrough=True)
    response.headers.add('Content-Range', 'bytes {0}-{1}/{2}'.format(start, end, total_size))
    response.headers.add('Accept-Ranges', 'bytes')
    
    return response
    
    
    
        
    
    
    
    
    