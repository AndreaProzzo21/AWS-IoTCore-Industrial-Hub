variable "factory_name" {

  type        = string

  description = "Nome identificativo della fabbrica"

}



variable "device_list" {

  type        = list(string)

  description = "Lista dei nomi dei macchinari/device in questa fabbrica"

} 