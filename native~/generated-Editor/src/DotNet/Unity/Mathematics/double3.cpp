#include <DotNet/Unity/Mathematics/double3.h>
#include <DotNet/Reinterop/ObjectHandle.h>
#include <DotNet/Reinterop/ReinteropNativeException.h>
#include <cstdint>

namespace DotNet::Unity::Mathematics {
struct double3;
}

namespace DotNet::Unity::Mathematics {

void (*double3::Construct_1B2M2Y8AsgTpgAmY7PhCfg)(::DotNet::Unity::Mathematics::double3* pReturnValue, void** reinteropException) = nullptr;


double3 double3::Construct()
{
    void* reinteropException = nullptr;
    double3 result;
    Construct_1B2M2Y8AsgTpgAmY7PhCfg(&result, &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return result;
}


void (*double3::Construct_vFScQRRHVnKCy1ZblYgxig)(double x, double y, double z, ::DotNet::Unity::Mathematics::double3* pReturnValue, void** reinteropException) = nullptr;


double3 double3::Construct(double x, double y, double z)
{
    void* reinteropException = nullptr;
    double3 result;
    Construct_vFScQRRHVnKCy1ZblYgxig(x, y, z, &result, &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return result;
}


double (*DotNet::Unity::Mathematics::double3::Property_get_Item)(const ::DotNet::Unity::Mathematics::double3* thiz, ::std::int32_t index, void** reinteropException) = nullptr;


double double3::operator[](::std::int32_t index) const {
    void* reinteropException = nullptr;
    auto result = Property_get_Item(&(*this), index, &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return result;
}


} // namespace DotNet::Unity::Mathematics


