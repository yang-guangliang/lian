# Underlying Layer

The underlying layer provides supports for other modules, including managing memory and storage, event-based plugin system, modeling external APIs. 

## Memory and File System (Loader)

To enhance the management of memory and files, particularly to mitigate memory insufficiency issues, we implemented a two-tier memory management system based on the LRU (Least Recently Used) algorithm, comprising the item layer and the bundle layer. Additionally, the bundle layer facilitates interaction with local hard disk storage, thereby enabling file management.  

## Plugin System (app_manager)

The unique characteristics of different programming languages require case-specific analysis and handling—for instance, JavaScript's prototype chain. To ensure the extensibility of the analysis tool, this system incorporates a plugin mechanism. When developers need to add a new plugin, they must first register it in `app_register.py` and `app_manager.py`, prepare the plugin's processing logic, and then trigger the plugin at the appropriate location via `AppManager.notify()`. Once triggered, the plugin returns its output along with its processing status.  

Taking a JavaScript prototype chain handler plugin as an example, after registering the plugin and preparing its processing logic, developers trigger it at the appropriate location:  

```python  
...  
event = EventData(  
            # The language to which this plugin applies  
            self.lang,  
            # The phase in which the plugin is invoked  
            EventKind.P2STATE_NEW_OBJECT_BEFORE,  
            {  
            # Input data for the plugin  
                "stmt_id": stmt_id,  
                ...              
            }  
        )  
# Trigger the plugin and retrieve its output and processing status  
app_return = self.app_manager.notify(event)  
# Determine subsequent analysis based on the plugin's processing status  
if event_return.is_event_unprocessed(app_return):  
    ...  
```  
