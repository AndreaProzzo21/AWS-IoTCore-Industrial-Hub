variable "aws_region" {
  type    = string
  default = "eu-central-1"
}

variable "factories" {
  type = map(object({
    devices = list(string)
  }))
  default = {
    "Metal-Stamping-Unit" = { 
      devices = ["Hydraulic-Press-01", "Hydraulic-Press-02", "Laser-Cutter-X1"] 
    }
    "Assembly-Line-Alpha" = { 
      devices = ["Robotic-Arm-Solder", "Vision-System-QC", "Torque-Controller-01"] 
    }
    "Automated-Warehouse" = { 
      devices = ["Conveyor-System-Belt", "AGV-Forklift-05", "Palletizer-Robot"] 
    }
  }
}