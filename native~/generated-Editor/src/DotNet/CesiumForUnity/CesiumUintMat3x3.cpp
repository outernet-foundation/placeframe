#include <DotNet/CesiumForUnity/CesiumUintMat3x3.h>
#include <DotNet/Reinterop/ObjectHandle.h>
#include <DotNet/Reinterop/ReinteropNativeException.h>
#include <DotNet/CesiumForUnity/CesiumUintVec3.h>
#include <cstdint>

namespace DotNet::CesiumForUnity {
struct CesiumUintVec3;
}
namespace DotNet::CesiumForUnity {
struct CesiumUintMat3x3;
}

namespace DotNet::CesiumForUnity {

void (*CesiumUintMat3x3::Construct_Y4SfatHSU__2N_SCzuuF_Fg)(const ::DotNet::CesiumForUnity::CesiumUintVec3* v0, const ::DotNet::CesiumForUnity::CesiumUintVec3* v1, const ::DotNet::CesiumForUnity::CesiumUintVec3* v2, ::DotNet::CesiumForUnity::CesiumUintMat3x3* pReturnValue, void** reinteropException) = nullptr;


CesiumUintMat3x3 CesiumUintMat3x3::Construct(const ::DotNet::CesiumForUnity::CesiumUintVec3& v0, const ::DotNet::CesiumForUnity::CesiumUintVec3& v1, const ::DotNet::CesiumForUnity::CesiumUintVec3& v2)
{
    void* reinteropException = nullptr;
    CesiumUintMat3x3 result;
    Construct_Y4SfatHSU__2N_SCzuuF_Fg(&v0, &v1, &v2, &result, &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return result;
}


void (*DotNet::CesiumForUnity::CesiumUintMat3x3::Property_get_Item)(const ::DotNet::CesiumForUnity::CesiumUintMat3x3* thiz, ::std::int32_t index, ::DotNet::CesiumForUnity::CesiumUintVec3* pReturnValue, void** reinteropException) = nullptr;


::DotNet::CesiumForUnity::CesiumUintVec3 CesiumUintMat3x3::operator[](::std::int32_t index) const {
    void* reinteropException = nullptr;
    ::DotNet::CesiumForUnity::CesiumUintVec3 result;
    Property_get_Item(&(*this), index, &result, &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return result;
}


} // namespace DotNet::CesiumForUnity


